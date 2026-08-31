# Écart avec l’implémentation actuelle

## Avis synthétique

La base technique est saine pour un MVP : pipeline explicite, sorties Pydantic strictes, normalisation prudente, validation de citations, calculs déterministes et règles séparées. Le frein principal n’est pas le moteur de règles ; c’est la pauvreté du modèle normalisé en amont.

Acquora reconnaît les huit familles demandées, mais n’en analyse réellement que quatre groupes : DPE, PV d’AG, finances de copropriété et diagnostics/ERP sous une forme très agrégée. Trois documents à forte valeur de rapprochement — taxe foncière, règlement de copropriété et carnet d’entretien — sont classés puis marqués terminés sans extraction structurée. Le système dispose déjà d’un début d’analyse croisée, mais celle-ci est limitée à cinq contrôles.

## Ce qui est déjà solide

- Les dix types documentaires, dont les huit du périmètre, existent dans [le classifieur](../../backend/app/documents/classification/models.py#L12-L23).
- Le DPE possède le modèle le plus riche, une vérification ADEME, des contrôles de validité et une provenance par page.
- Les normaliseurs rejettent les valeurs non supportées par le texte source au lieu de les persister.
- L’arithmétique des charges et échéances est déterministe, notamment dans [la normalisation financière](../../backend/app/property/normalization/financials.py#L134-L172).
- Les findings ont des codes stables, des statuts, une gravité, une confiance et des sources dans [le modèle de risque](../../backend/app/risks/models/findings.py#L13-L70).
- Un premier réconciliateur construit une chronologie et génère cinq familles de contrôles dans [reconciliation.py](../../backend/app/property/reconciliation.py#L46-L256).

## Couverture actuelle par document

| Document | État actuel | Principale limite | Priorité |
|---|---|---|---|
| DPE | Extraction dédiée riche + ADEME + règles | Manquent enveloppe détaillée, scénarios de travaux structurés, confort d’été, énergie finale, contexte locatif/audit et règles datées 2024/2026/2027 | P1 |
| Dossier de diagnostics | Un modèle commun avec 6 types et 6 résultats | Aucun niveau d’anomalie, localisation technique, périmètre non visité, concentration plomb, état amiante, termites, assainissement ou bruit | P0 |
| État des risques | Réutilise le diagnostic générique `environmental_risk` | Perd PPR, aléas, zonages, sinistres, parcelle, SIS, radon, recul du trait de côte, OLD et cartes | P0 |
| Taxe foncière | Classée uniquement | Aucun fait, KPI ni règle | P1 |
| PV d’AG | Travaux/problèmes sous 12 catégories et 7 statuts | Résolutions, votes, budgets, comptes, assurances, procédures, prêts, PPT/DTG, gouvernance et liens projet trop pauvres | P0 |
| Charges et comptes | 5 catégories de lignes financières | Absence de compte lot, annexes comptables, fournisseurs, trésorerie, budgets/réalisé, nombre de débiteurs, clés et prêts | P0 |
| Règlement/EDD | Classé uniquement | Aucun lot, tantième, clé, destination, droit ou restriction exploitable | P0 |
| Carnet d’entretien | Classé uniquement | Aucun équipement, contrat, chantier, garantie ou historique exploitable | P1 |

La cause technique directe apparaît dans [document_processing.py](../../backend/app/jobs/document_processing.py#L17-L24) et [structured_service.py](../../backend/app/property/normalization/structured_service.py#L59-L73) : seuls AG, finances, diagnostics et état des risques sont routés vers l’extracteur structuré, en plus du service DPE séparé. Les autres types sont simplement terminés par [document_processing.py](../../backend/app/jobs/document_processing.py#L61-L70).

## Limites métier importantes

### 1. Le DDT et l’ERP sont trop compressés

Le modèle [NormalizedDiagnosticFinding](../../backend/app/property/normalization/diagnostics.py#L19-L67) ne conserve que le type, un résultat générique, une description, deux dates, une surface et une source. Ce schéma ne permet pas de règles fiables sur :

- plomb au-dessus de 1 mg/cm² et état de dégradation ;
- amiante par matériau, zone, état et préconisation ;
- anomalies gaz A1/A2/DGI ou anomalies électriques par organe ;
- zones inaccessibles ;
- termites, assainissement ou bruit aérien ;
- PPR, parcelle, niveau d’aléa, SIS, sinistres indemnisés et travaux non réalisés.

Conséquence : deux constats radicalement différents deviennent tous deux `ANOMALY` ou `RISK_IDENTIFIED`, puis reçoivent souvent la même gravité.

### 2. Le modèle AG confond des projets distincts

Le modèle [AgItemCandidate](../../backend/app/property/normalization/ag_minutes.py#L19-L78) est une bonne première passe, mais une résolution n’a pas d’identifiant de projet stable, de résultat de vote détaillé, de clé de charges, de calendrier d’appels, de prestataire, de version de devis ou de lien vers une résolution antérieure.

Dans les règles, plusieurs occurrences de même `kind` peuvent donc être rapprochées alors qu’elles concernent des chantiers différents. À l’inverse, un même projet reformulé entre deux AG peut ne pas être relié.

### 3. Les comptes ne permettent pas d’évaluer la santé de la copropriété

Les cinq catégories du [modèle financier](../../backend/app/property/normalization/financials.py#L19-L61) couvrent les coûts visibles mais pas les mécanismes d’une copropriété fragile : sommes exigibles, nombre de lots et de débiteurs, dettes fournisseurs, trésorerie, créances, approbation des comptes, budget/réalisé, emprunts et ventilation par poste.

Le seuil légal d’alerte sur les impayés ne peut donc pas être calculé. Un montant brut de 10 000 € n’a pourtant pas la même signification dans une copropriété de 6 lots et dans une copropriété de 500 lots.

### 4. Des seuils absolus produisent des gravités peu contextuelles

Exemples actuels :

- quote-part élevée à 5 000/10 000 € dans [coproperty.py](../../backend/app/risks/rules/coproperty.py#L61-L76) ;
- impayés significatifs à 5 000/10 000 € dans [coproperty.py](../../backend/app/risks/rules/coproperty.py#L78-L98) ;
- hausse de charges à 500 € ou 20 % dans [financials.py](../../backend/app/property/normalization/financials.py#L150-L170) ;
- coût énergétique haut à 2 000/3 000 € dans [dpe.py](../../backend/app/risks/rules/dpe.py#L122-L141).

Ces seuils peuvent rester comme garde-fous temporaires, mais la gravité devrait combiner montant du lot, prix d’achat, surface, charges annuelles, budget copropriété, fonds disponible et projet utilisateur. Les seuils réglementaires, eux, doivent rester distincts et versionnés.

### 5. Un montant collectif peut ressembler à une exposition du lot

Pour un travail voté, la règle utilise la quote-part si elle existe, sinon le montant collectif comme `amount_eur` dans [coproperty.py](../../backend/app/risks/rules/coproperty.py#L40-L58). Les paiements futurs font un repli comparable tout en le signalant dans le texte. L’interface doit typer le montant (`lot_share`, `collective_total`, `estimate`, `confirmed_due`) pour éviter une addition ou une lecture trompeuse.

### 6. Le rapprochement de projets est lexical et fragile

La fonction [_subject_matches](../../backend/app/property/reconciliation.py#L90-L95) considère qu’un mot d’au moins cinq caractères commun suffit à relier travaux et appel. « Réfection toiture bâtiment A » et « diagnostic toiture bâtiment B » peuvent se rapprocher à tort ; « étanchéité terrasse » et « reprise complexe bitumineux » peuvent être manqués.

Il faut une entité `WorkProject` avec composant, bâtiment, résolution, dates, prestataire et montants, puis un rapprochement scoré et auditable. Un LLM peut proposer le lien, mais une règle doit l’accepter seulement sur des critères explicites.

### 7. La couverture documentaire manquante est partielle

[missing_documents.py](../../backend/app/risks/rules/missing_documents.py#L89-L245) contrôle DPE, PV, finances et justificatifs de travaux. Il ne contrôle pas le DDT, l’ERP, la taxe foncière, le règlement/EDD, le carnet, ni les pièces conditionnelles telles que DTA, PPPT/PPT, état daté et audit énergétique.

La logique « attendu » doit devenir une matrice d’applicabilité fondée sur : type de bien, copropriété, année/permis, âge des installations, commune/parcelle, assainissement, classe DPE, usage actuel et projet acheteur.

### 8. Le finding n’embarque pas l’action

[RiskFinding](../../backend/app/risks/models/findings.py#L51-L70) n’a pas de champ pour :

- action acheteur ;
- interlocuteur ;
- pièce à demander ;
- échéance de l’action ;
- condition d’applicabilité ;
- base légale/version de règle ;
- type et périmètre d’un montant.

Ces champs ne devraient pas être enfouis dans une explication LLM : ils sont déterministes, filtrables et testables.

### 9. Les sources externes et les périmètres sont mal représentés

`SourceReference` exige un document et une page. C’est très bien pour un PDF, mais insuffisant pour représenter proprement une réponse ADEME, une règle versionnée, une donnée Géorisques ou un calcul dérivé de plusieurs faits. Il manque aussi les notions de bâtiment, lot, partie privative/commune, zone inspectée et champ exact dans un tableau.

Le modèle devrait séparer :

- `DocumentEvidence` : document, page, citation, zone/table ;
- `ExternalEvidence` : fournisseur, identifiant, date de consultation, URL/version ;
- `DerivedEvidence` : règle, version, opérandes et formule.

### 10. Les points rassurants sont trop étroits

La génération actuelle produit surtout des constats favorables DPE et diagnostics. Elle ne peut pas encore valoriser de façon fiable : baisse durable des impayés, fonds couvrant les travaux, comptes approuvés, chantier réceptionné sans réserve, contrat d’entretien à jour, absence explicite de sinistre ou compatibilité du règlement avec le projet.

Il faut toutefois conserver une exigence forte : « rien trouvé » n’est jamais rassurant sans mesure de couverture.

## Architecture cible minimale

Le moteur existant peut être conservé en ajoutant quatre couches simples.

```text
Extracteurs par famille
→ faits normalisés typés et sourcés
→ entités de dossier (Property, Lot, Component, WorkProject, AccountingPeriod)
→ rapprochements et calculs déterministes
→ findings avec action, applicabilité et preuves
```

### Noyau de faits commun

Chaque fait devrait au minimum porter :

```text
fact_code
value + unit
scope: property/building/lot/component/coproperty
entity_id
effective_date or covered_period
evidence[]
extraction_status: confirmed/ambiguous/not_found
```

Les modèles documentaires restent spécifiques. Il ne faut pas créer un schéma générique qui ferait perdre les concepts propres au CREP, à l’ERP ou aux annexes comptables.

### Entités de rapprochement

- `PropertyIdentity` et `LotIdentity`
- `BuildingComponent` : toiture, façade, structure, ascenseur, chauffage, ventilation, canalisation
- `WorkProject` : sujet, bâtiment, composant, résolution, statut, coût collectif, quote-part, échéances
- `AccountingPeriod` : budget, réalisé, approbation, trésorerie, impayés, fournisseurs
- `DiagnosticAssessment` : type, zone, élément, mesure, état, préconisation, validité
- `RegulatoryApplicability` : règle, juridiction, date d’effet, faits déclencheurs

## Ordre d’implémentation recommandé

### P0 — rendre les conclusions fiables

1. Ajouter à `RiskFinding` l’action, l’interlocuteur, la pièce demandée, l’échéance, le type de montant et la version de règle.
2. Créer une matrice d’applicabilité des documents et diagnostics.
3. Remplacer le diagnostic générique par des sous-modèles DDT et un modèle ERP dédié.
4. Enrichir AG et finances avec `project_id`, résolution/vote, budget/réalisé, impayés, fournisseurs, trésorerie, prêt et statut des comptes.
5. Extraire règlement/EDD : lots, destination, parties, tantièmes et clés. C’est le multiplicateur principal des analyses croisées.
6. Introduire `WorkProject` et typer strictement tous les montants.

### P1 — augmenter fortement le rappel des risques

1. Ajouter carnet d’entretien et taxe foncière.
2. Structurer les recommandations DPE et composants énergétiques.
3. Implémenter les croisements des sections A à F du catalogue par lots de 5 à 10 règles.
4. Agréger coûts confirmés, coûts potentiels et coûts collectifs dans trois totaux séparés.
5. Étendre les points rassurants avec une condition de couverture explicite.

### P2 — calibrer et surveiller

1. Constituer des fixtures par type de document et des dossiers complets multi-documents.
2. Mesurer extraction champ par champ, exactitude des montants/dates/pages, rappel des risques et faux rapprochements.
3. Versionner les règles légales par `effective_from`/`effective_to` et exécuter des tests temporels.
4. Ajouter une file de revue des faits ambigus et des rapprochements à confiance moyenne.
5. Mesurer la couverture de chaque document : pages lisibles, sections attendues trouvées, zones exclues et tables reconnues.

## Limite produit irréductible

Même après implémentation complète du catalogue, Acquora restera une analyse documentaire. Elle ne détectera pas de façon fiable un vice non écrit, une fissure masquée, une humidité récente, un bruit réel, un équipement remplacé sans facture, une fraude documentaire ou une décision informelle non versée au dossier. Le meilleur rapport doit donc conclure par les contrôles physiques et professionnels encore nécessaires, et non par un score global de « sécurité d’achat ».
