# Description produit — Analyse de documents avant compromis immobilier

## 1. Vision du produit

Application web permettant à un acheteur immobilier d’importer le dossier transmis par l’agence, le vendeur ou le notaire, puis d’obtenir en quelques minutes une lecture claire des documents disponibles, des pièces manquantes, des risques détectés et des questions à poser avant de signer le compromis.

Le produit doit réduire la charge de lecture sans masquer l’information : l’utilisateur voit d’abord une synthèse courte et actionnable, puis ouvre les détails uniquement s’il le souhaite. Chaque constat doit être relié à sa source exacte dans un document.

## 2. Utilisateur et périmètre initial

- Utilisateur principal : particulier achetant un appartement en copropriété en France.
- Moment d’usage : avant la signature du compromis, éventuellement après réception d’une nouvelle version du dossier.
- Entrées : PDF et images transmis par l’agence, le vendeur ou le notaire.
- Sorties : synthèse du dossier, documents présents et manquants, alertes hiérarchisées, informations clés, questions recommandées et rapport partageable.
- Le service fournit une aide à la lecture et à la décision, pas une certification du bien ni un conseil juridique, notarial ou technique.

## 3. Principes d’expérience utilisateur

1. **Une adresse = un dossier d’acquisition.**
2. **Synthèse avant détails.** Aucun long pavé sur l’écran principal.
3. **Progressive disclosure.** Une carte résume un point en une ou deux phrases ; un clic ouvre l’explication, l’impact, la recommandation et la source.
4. **Priorité à l’action.** Chaque alerte indique ce que l’acheteur doit vérifier, demander ou négocier.
5. **Traçabilité systématique.** Aucun constat ne doit être présenté sans document, page et extrait source, sauf s’il s’agit explicitement d’une pièce manquante ou d’une déduction.
6. **Incertitude visible.** Le produit distingue les faits extraits, les calculs, les déductions et les informations non vérifiables.
7. **Langage simple.** Les termes immobiliers sont expliqués à la demande.

## 4. Parcours principal

### 4.1 Création d’un dossier

L’utilisateur crée un dossier avec :

- adresse du bien ;
- type de bien ;
- prix affiché ou envisagé, facultatif ;
- surface et nombre de lots, facultatifs ;
- date prévue du compromis, facultative.

Il peut ensuite importer tous les fichiers en une fois ou progressivement.

### 4.2 Import et traitement

L’import accepte plusieurs PDF et images, avec glisser-déposer, sélection de fichiers et ajout ultérieur. L’interface affiche pour chaque fichier : nom, taille, statut d’envoi, statut d’analyse et erreur éventuelle.

Après import, le système :

- vérifie que le fichier est lisible, non vide et non dupliqué ;
- applique OCR si nécessaire ;
- sépare les documents regroupés dans un même PDF ;
- reconnaît le type de chaque document ;
- extrait les informations structurées et leurs sources ;
- détecte les incohérences, risques et éléments manquants ;
- signale les pages illisibles ou les analyses incertaines ;
- met à jour la synthèse du dossier.

L’utilisateur peut corriger le type ou le nom d’un document mal identifié et relancer son analyse.

### 4.3 Consultation des résultats

Le tableau de bord du dossier affiche en priorité :

- un niveau de complétude documentaire ;
- le nombre d’alertes critiques, importantes et informatives ;
- les trois à cinq principaux points à vérifier avant signature ;
- les documents manquants ou illisibles ;
- les chiffres clés du bien et de la copropriété ;
- la date de la dernière analyse.

Chaque section est cliquable et mène à une vue filtrée ou à un panneau de détail.

## 5. Gestion des documents

### 5.1 Bibliothèque du dossier

La bibliothèque liste les documents avec leur type, date, statut d’analyse, qualité de lecture et éventuelle version. Elle permet de :

- prévisualiser le document ;
- rechercher un mot ou une expression ;
- filtrer par catégorie ou statut ;
- renommer, reclasser, remplacer ou supprimer un fichier ;
- ajouter une version plus récente sans perdre l’historique ;
- voir les informations et alertes issues de ce document.

### 5.2 Types de documents à reconnaître

Le produit doit au minimum gérer :

- projet de compromis ou promesse de vente ;
- titre de propriété et descriptif du lot ;
- règlement de copropriété, état descriptif de division et modificatifs ;
- procès-verbaux des assemblées générales des trois dernières années ;
- fiche synthétique de copropriété ;
- carnet d’entretien de l’immeuble ;
- plan pluriannuel de travaux, projet de PPT ou diagnostic technique global ;
- relevés de charges, appels de fonds, budget prévisionnel et état financier de copropriété ;
- pré-état daté ou état daté ;
- taxe foncière ;
- DPE et audit énergétique éventuel ;
- diagnostics amiante, plomb, termites, gaz, électricité, ERP, bruit et assainissement selon le bien ;
- mesurage loi Carrez ;
- plans, factures de travaux, autorisations de copropriété et autorisations d’urbanisme ;
- bail ou éléments d’occupation si le bien n’est pas libre ;
- autres pièces non reconnues, conservées sous la catégorie « Autre ».

La liste des documents attendus doit être adaptée au type de bien, à son ancienneté, à sa localisation et aux informations déjà connues. Une pièce peut être obligatoire, recommandée, non applicable ou impossible à déterminer.

## 6. Analyse et restitution

### 6.1 Informations clés extraites

Le système extrait et consolide notamment :

- adresse, désignation et numéros de lots ;
- surface privative, surface habitable et annexes ;
- prix, mobilier, honoraires et dépôt de garantie lorsqu’un avant-contrat est présent ;
- identité et qualité des parties ;
- conditions suspensives et dates importantes ;
- occupation du bien, servitudes et droits particuliers ;
- étiquette DPE, consommation, émissions, date et validité du diagnostic ;
- anomalies des diagnostics techniques ;
- montant des charges, fonds travaux, impayés et dettes de copropriété ;
- travaux votés, réalisés, refusés ou envisagés, avec montants et échéances ;
- tantièmes du lot et répartition des dépenses lorsque disponibles ;
- taxe foncière ;
- sinistres, procédures, litiges et problèmes récurrents mentionnés ;
- restrictions d’usage, de location ou de travaux prévues par la copropriété.

En cas de valeurs différentes entre documents, le système ne choisit pas silencieusement : il affiche l’incohérence, les valeurs concurrentes et leurs sources.

### 6.2 Catégories de risques

Les alertes couvrent au minimum :

- **dossier incomplet** : document attendu absent, expiré, incomplet ou illisible ;
- **coûts futurs** : travaux votés ou probables, appels de fonds, ravalement, toiture, ascenseur, chauffage, performance énergétique ;
- **santé financière de la copropriété** : impayés, dette fournisseurs, trésorerie faible, budget en hausse, procédures ;
- **état du bien et de l’immeuble** : anomalies électriques ou gaz, amiante, plomb, humidité, sinistres, entretien insuffisant ;
- **performance énergétique** : mauvaise classe, interdictions ou contraintes locatives applicables, travaux recommandés, incohérence du DPE ;
- **juridique et contractuel** : servitude, condition défavorable ou manquante, occupation, litige, droit de jouissance, lot non conforme ;
- **copropriété et usages** : restriction de location, activité professionnelle, animaux, travaux privatifs, usage des annexes ;
- **incohérences** : adresse, surface, lot, montant, date ou identité contradictoire entre pièces ;
- **échéances** : diagnostic expiré, délai court, AG imminente ou appel de fonds proche.

### 6.3 Format d’une alerte

Chaque alerte contient :

- un titre court ;
- une sévérité : critique, importante ou information ;
- une catégorie ;
- un résumé d’une à deux phrases ;
- le fait détecté ;
- l’impact potentiel pour l’acheteur ;
- l’action recommandée ;
- la ou les sources exactes : document, page et extrait ;
- un niveau de confiance ;
- un statut utilisateur : à traiter, vérifié, accepté ou ignoré ;
- une note personnelle facultative.

Une sévérité élevée ne doit jamais être fondée uniquement sur un faible niveau de confiance sans avertissement explicite.

### 6.4 Questions recommandées

Le produit génère une liste courte de questions adaptées au dossier, regroupées par destinataire : agent immobilier, vendeur, syndic, notaire ou diagnostiqueur. Chaque question indique pourquoi elle est posée et à quelle alerte ou pièce manquante elle répond.

L’utilisateur peut copier une question, la marquer comme posée, saisir la réponse et joindre un nouveau document. Une réponse ne ferme pas automatiquement l’alerte : elle doit être confirmée par l’utilisateur ou par une pièce justificative.

### 6.5 Estimations financières

Lorsque les données le permettent, le produit synthétise :

- charges annuelles connues ;
- taxe foncière ;
- travaux déjà votés restant à payer ;
- autres coûts explicitement documentés ;
- montants seulement estimés, clairement distingués des montants certains.

Le produit ne doit pas inventer de coût. Toute estimation utilise une hypothèse visible et modifiable. Les totaux distinguent « certain », « probable » et « non chiffrable ».

## 7. Lecture des sources

Depuis une alerte ou une donnée, l’utilisateur peut ouvrir le document directement à la bonne page, avec le passage concerné mis en évidence. Il peut naviguer entre les sources sans perdre le contexte de l’alerte.

Si l’extrait provient d’un OCR incertain, l’interface invite à vérifier visuellement la page. Les déductions reliant plusieurs documents affichent toutes les sources utilisées.

## 8. Rapport et partage

L’utilisateur peut générer un rapport synthétique comprenant :

- identification du bien et date d’analyse ;
- état de complétude du dossier ;
- points critiques et importants ;
- chiffres clés ;
- documents manquants ;
- questions restant à poser ;
- avertissement sur les limites du service.

Le rapport peut être exporté en PDF. Une version partageable par lien peut être proposée avec accès en lecture seule, expiration et révocation. Les documents originaux ne doivent pas être accessibles au destinataire sauf choix explicite de l’utilisateur.

## 9. Mise à jour du dossier

Lorsqu’un document est ajouté ou remplacé, seules les analyses affectées sont recalculées. L’interface indique clairement :

- les nouveaux constats ;
- les alertes résolues ou modifiées ;
- les valeurs ayant changé ;
- la version du document à l’origine du changement.

L’historique permet de comprendre l’évolution du dossier sans présenter une complexité de versionnement sur l’écran principal.

## 10. Gestion du compte et des données

- création de compte, connexion et réinitialisation du mot de passe ;
- liste des dossiers avec adresse, avancement, alertes et dernière activité ;
- renommage, archivage et suppression d’un dossier ;
- téléchargement des documents et du rapport ;
- suppression définitive des données avec confirmation ;
- politique de conservation visible ;
- chiffrement des données en transit et au repos ;
- accès strictement limité au propriétaire et aux personnes invitées ;
- journalisation des accès et des opérations sensibles ;
- consentement explicite avant utilisation éventuelle des données à des fins d’amélioration.

## 11. États et erreurs à prévoir

L’interface doit traiter explicitement :

- dossier vide ;
- import en cours ;
- analyse en attente, en cours, terminée ou échouée ;
- fichier protégé par mot de passe, corrompu, trop volumineux ou non pris en charge ;
- document partiellement illisible ;
- type de document inconnu ;
- extraction peu fiable ;
- aucun risque détecté, sans prétendre que le bien est sans risque ;
- service d’analyse temporairement indisponible ;
- nouvelle version d’un résultat disponible.

Chaque erreur doit proposer une prochaine action concrète : réessayer, remplacer le fichier, corriger son type ou contacter le support.

## 12. Écrans minimums du MVP

1. Connexion et création de compte.
2. Liste des dossiers.
3. Création d’un dossier et import des fichiers.
4. Tableau de bord de synthèse d’un dossier.
5. Liste filtrable des alertes et panneau de détail.
6. Checklist des documents présents, manquants et non applicables.
7. Bibliothèque et lecteur de document avec source surlignée.
8. Informations clés et incohérences.
9. Questions à poser et suivi des réponses.
10. Génération et consultation du rapport.
11. Paramètres du dossier, partage et suppression.

## 13. Règles fonctionnelles impératives

- Une information générée par l’analyse doit toujours conserver le lien avec sa ou ses sources.
- Le système ne doit jamais présenter une information supposée comme un fait certain.
- L’absence d’alerte ne doit jamais être formulée comme une garantie d’absence de risque.
- Les obligations documentaires et règles réglementaires doivent être datées et versionnées ; si leur applicabilité est incertaine, le produit le dit.
- Une suppression de document recalcule ou invalide les résultats qui en dépendent.
- Toute correction manuelle est identifiable et conservée lors d’une nouvelle analyse, sauf conflit signalé.
- Les alertes critiques restent visibles dans la synthèse tant qu’elles ne sont pas explicitement traitées.
- Les informations sensibles ne sont jamais exposées dans les URL, journaux applicatifs ou rapports partagés par défaut.

## 14. Hors périmètre initial

- estimation automatique de la valeur de marché du bien ;
- recommandation ferme d’acheter ou de renoncer ;
- garantie juridique, technique ou financière ;
- remplacement du notaire, du diagnostiqueur, de l’architecte ou d’un audit physique ;
- négociation ou envoi automatique de messages au vendeur ;
- signature électronique du compromis ;
- gestion complète d’une maison individuelle, d’un immeuble entier, d’un terrain ou d’un achat professionnel, à traiter dans des extensions ultérieures.

## 15. Critères de réussite du produit

Le MVP est réussi si un acheteur peut, sans connaissance immobilière particulière :

- créer un dossier et importer ses pièces sans assistance ;
- comprendre en moins d’une minute si le dossier est complet et quels sont les principaux risques ;
- vérifier chaque constat dans le document source ;
- identifier les questions prioritaires à poser avant le compromis ;
- intégrer de nouvelles pièces et voir ce qui a changé ;
- partager une synthèse compréhensible avec son notaire ou un proche.

## 16. Hypothèses à confirmer avant implémentation détaillée

- Le MVP cible uniquement les appartements en copropriété situés en France.
- Le premier utilisateur est l’acheteur ; il n’existe pas encore d’espace distinct pour les agences ou les notaires.
- L’analyse est asynchrone et peut durer plusieurs minutes.
- Le PDF est le format d’export prioritaire.
- Les liens de partage et les estimations de coûts peuvent être reportés après le premier MVP si nécessaire.
