# Intégration du dossier de démonstration

## Résultat attendu

Après sa première authentification, chaque utilisateur voit un dossier « 24 rue des Tisseurs, 69004 Lyon • Démo » dans la liste de ses dossiers. Il est visuellement distinct, en lecture seule et consultable avec les mêmes écrans de synthèse, rapport, documents, sources et visionneuse PDF qu'un dossier réel.

Le chemin de lecture ne doit pas diverger du produit réel. La démo utilise les mêmes tables, modèles Pydantic, règles déterministes, assembleur de rapport, contrôles d'autorisation et URLs signées. Seul le provisionnement initial est spécifique.

## Modèle de données proposé

Ajouter à `analysis_cases` :

- `case_kind`, enum contrôlé `user` ou `demo`, valeur par défaut `user` ;
- `template_key`, nullable, valeur `lyon_v1` pour la démo ;
- une contrainte unique partielle sur `(user_id, template_key)` quand `case_kind = 'demo'`.

Ajouter à `documents` :

- `storage_ownership`, enum contrôlé `case` ou `shared_demo`, valeur par défaut `case` ;
- supprimer l'unicité globale de `storage_key`, car plusieurs lignes appartenant à des utilisateurs différents référenceront le même objet privé de démonstration ;
- conserver l'unicité existante `(analysis_case_id, sha256)`.

Exposer `case_kind` dans `AnalysisCaseRead`. Aucun contenu synthétique ne doit être inféré depuis une couleur ou depuis le titre.

## Provisionnement idempotent

Créer un service backend `DemoCaseProvisioner` et une commande d'administration `seed_demo_template`.

La commande d'administration :

1. vérifie les empreintes du `manifest.json` ;
2. charge les 18 PDF sous `demo-templates/lyon_v1/<sha256>.pdf` dans le bucket privé ;
3. construit une fixture canonique avec extraction des 95 pages, classification, données normalisées, constats et rapport ;
4. valide cette fixture avec les modèles Pydantic actuels avant de la publier.

Le provisionneur utilisateur :

1. verrouille l'utilisateur ou s'appuie sur la contrainte unique partielle ;
2. crée le cas `demo` s'il n'existe pas ;
3. copie les petites lignes relationnelles de la fixture canonique avec de nouveaux UUID ;
4. remappe tous les `document_id` contenus dans les sources et citations ;
5. référence les PDF partagés avec `storage_ownership = 'shared_demo'` ;
6. valide puis commit toute la copie dans une seule transaction.

Le provisionnement peut être déclenché lors de la première requête authentifiée qui liste les dossiers. Il doit rester idempotent et sûr en cas de deux requêtes concurrentes. Une alternative plus explicite consiste à appeler une route interne depuis le callback de première connexion, mais elle ajoute un couplage inutile entre Auth.js et FastAPI.

## Pourquoi pré-calculer l'analyse

Il ne faut pas repasser les 18 PDF dans Xberg et le LLM pour chaque nouvel inscrit. Cela augmenterait le délai de première ouverture, le coût, les risques de variation et l'exposition inutile à des prestataires tiers.

La fixture canonique est toutefois produite par le pipeline normal : extraction, classification, normalisation, règles, rapprochements et rapport. Elle est ensuite figée et clonée. Une tâche CI la régénère lorsque les versions de prompts, schémas ou règles changent, puis compare les résultats au manifeste attendu. Ainsi, la démo reste représentative du workflow réel sans l'exécuter à chaque inscription.

## Lecture, sécurité et suppression

- Toutes les routes continuent à appeler les méthodes `get_owned_*`. Chaque copie de démonstration appartient donc bien à son utilisateur.
- Les PDF restent privés et sont consultés via les URLs signées existantes.
- Les routes de mutation refusent les cas `case_kind = 'demo'` avec une réponse `409` et un message clair. Cela concerne upload, suppression, retraitement, changement de type, rafraîchissement manuel et revue des constats.
- La suppression d'un utilisateur supprime ses lignes de démo, mais jamais les objets marqués `shared_demo`.
- Une tâche d'administration peut retirer une version de template uniquement lorsqu'aucune ligne ne la référence plus.
- Aucun document de démonstration n'est placé dans `frontend/public`.

## Interface

Dans la liste des dossiers, utiliser une surface de carte différente mais sans bordure d'accent, conformément au design system. Ajouter un badge explicite « Démo » et un texte accessible « dossier de démonstration en lecture seule ». La distinction ne doit pas reposer uniquement sur la couleur.

Dans le dossier, afficher un bandeau discret rappelant que les données sont fictives. Masquer ou désactiver les actions de modification. Les écrans de rapport, documents, détails DPE, citations et PDF restent les composants existants.

Ne pas sélectionner automatiquement la démo si l'utilisateur possède déjà un dossier réel actif. À la première connexion sans dossier actif, l'ouverture automatique de la démo est acceptable.

## Tests indispensables

- un utilisateur reçoit exactement une démo, même sous requêtes concurrentes ;
- deux utilisateurs possèdent des cas et UUID distincts, mais peuvent référencer les mêmes objets privés ;
- un utilisateur ne peut jamais lire la copie de l'autre ;
- les mutations sur la démo sont refusées, celles des dossiers réels restent inchangées ;
- la suppression d'une copie ne supprime pas un PDF partagé ;
- chaque source du rapport pointe vers le bon document cloné et la bonne page ;
- les 18 PDF passent la validation MIME, signature et taille ;
- l'extraction textuelle retrouve les valeurs sentinelles du manifeste ;
- les constats attendus restent stables lors d'une régénération de fixture ;
- le frontend affiche le badge et le libellé accessible sur petit écran.

## Déploiement conseillé

1. fusionner la migration et les garde-fous backend ;
2. envoyer la version `lyon_v1` dans le stockage privé via la commande d'administration ;
3. vérifier la fixture et ses citations en préproduction ;
4. déployer l'interface avec le badge et le mode lecture seule ;
5. activer le provisionnement derrière un feature flag serveur ;
6. observer taux d'ouverture, erreurs de provisionnement et passages de la démo vers un premier dossier réel ;
7. généraliser après validation, puis retirer le flag si le comportement est stable.
