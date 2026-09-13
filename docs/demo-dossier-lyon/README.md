# Dossier de démonstration Lyon

Ce répertoire contient un dossier immobilier entièrement synthétique pour un appartement fictif situé au **24 rue des Tisseurs, 69004 Lyon**.

Toutes les personnes, entreprises, références, montants et caractéristiques sont fictifs. Chaque page PDF porte la mention visible « DOCUMENT SYNTHÉTIQUE DE DÉMONSTRATION • SANS VALEUR CONTRACTUELLE ». Ces fichiers ne doivent jamais être présentés comme des documents officiels, contractuels ou issus d'une administration.

## Contenu

Le jeu couvre les dix catégories documentaires actuellement reconnues par l'application : DPE, procès-verbaux d'AG, diagnostics, comptes, charges, appel de fonds travaux, taxe foncière, règlement de copropriété, carnet d'entretien et état des risques. Il ajoute les pièces de contexte attendues dans un dossier de copropriété, comme la fiche synthétique, le DTG avec projet de plan pluriannuel, le carnet d'information du logement, une attestation de propriété et une notice d'information.

La version courante contient 18 PDF et 48 pages compactes. Les documents restent sans identité visuelle produit. Hors DPE, ils reprennent volontairement l'aspect d'exports bureautiques anciens : polices sérif, tableaux simples, en-têtes administratifs, texte dense et mise en page en niveaux de gris. Les procès-verbaux contiennent le détail des présences, budgets, contrats, travaux, votes, questions diverses et annexes. Le DPE utilise les huit pages du modèle national officiel « appartement existant » de septembre 2025 : étiquettes énergie et climat, déperditions, confort, consommations, équipements, travaux et annexes techniques. Les données du spécimen sont supprimées puis remplacées par celles du scénario lyonnais. Aucune donnée privée des DPE locaux de référence n'est reprise. La provenance du modèle et des polices est documentée dans [scripts/assets/README.md](../../scripts/assets/README.md).

Le fichier `manifest.json` décrit le cas, les indices de classification, les périodes, les empreintes SHA-256 et les signaux que l'analyse doit retrouver.

## Régénération

Depuis la racine du dépôt :

```bash
uv run scripts/generate_demo_dossier.py
```

`uv` installe la version de PyMuPDF déclarée dans le script. Le modèle officiel et les polices IBM Plex sont versionnés localement ; aucun PDF privé ni téléchargement de modèle n'est nécessaire à la régénération. Les autres documents utilisent la bibliothèque standard Python. Tous les PDF contiennent du texte sélectionnable et des flux compressés.

Le DPE reste une simulation de présentation, sans calcul 3CL certifié. Ses totaux sont cohérents avec le scénario : 10 300 kWh d'énergie finale, 19 570 kWh d'énergie primaire et 302 kWh/m²/an pour 64,80 m². Le coefficient électrique de 1,9 correspond à la date fictive du 25 août 2026 ([source ministérielle](https://www.ecologie.gouv.fr/presse/evolution-du-calcul-du-dpe-1er-janvier-2026-favoriser-lelectrification-du-chauffage)).

Contrôles de régénération, de cohérence des montants, de pagination, de données résiduelles et d'empreintes du manifeste :

```bash
uv run scripts/test_demo_dpe.py
```

## Garde-fous de production

Ces fichiers sont des sources de démonstration versionnées. Ils doivent être placés dans le stockage objet privé, jamais dans `frontend/public`. L'application doit provisionner un dossier de démonstration personnel et en lecture seule pour chaque utilisateur authentifié, tout en réutilisant ces objets communs sans autoriser leur suppression.
