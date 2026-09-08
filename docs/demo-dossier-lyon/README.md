# Dossier de démonstration Lyon

Ce répertoire contient un dossier immobilier entièrement synthétique pour un appartement fictif situé au **24 rue des Tisseurs, 69004 Lyon**.

Toutes les personnes, entreprises, références, montants et caractéristiques sont fictifs. Chaque page PDF porte la mention visible « DOCUMENT SYNTHÉTIQUE DE DÉMONSTRATION • SANS VALEUR CONTRACTUELLE ». Ces fichiers ne doivent jamais être présentés comme des documents officiels, contractuels ou issus d'une administration.

## Contenu

Le jeu couvre les dix catégories documentaires actuellement reconnues par l'application : DPE, procès-verbaux d'AG, diagnostics, comptes, charges, appel de fonds travaux, taxe foncière, règlement de copropriété, carnet d'entretien et état des risques. Il ajoute les pièces de contexte attendues dans un dossier de copropriété, comme la fiche synthétique, le DTG avec projet de plan pluriannuel, le carnet d'information du logement, une attestation de propriété et une notice d'information.

La version courante contient 18 PDF et 95 pages. Les documents restent sans identité visuelle produit. Le DPE reprend la hiérarchie visuelle verte et rose du formulaire standardisé, avec un bandeau magenta répété sur chaque page pour signaler les données entièrement fictives. Le DDT reprend la densité et le découpage habituels d'un rapport professionnel. Aucun nom, identifiant, chiffre ou autre donnée du dossier local utilisé comme référence visuelle n'a été copié.

Le fichier `manifest.json` décrit le cas, les indices de classification, les périodes, les empreintes SHA-256 et les signaux que l'analyse doit retrouver.

## Régénération

Depuis la racine du dépôt :

```bash
python3 scripts/generate_demo_dossier.py
```

Le générateur utilise uniquement la bibliothèque standard Python. Les PDF contiennent du texte sélectionnable, les flux sont compressés et les polices PDF intégrées sont utilisées. Le dossier complet reste donc très léger et compatible avec le pipeline normal d'extraction.

## Garde-fous de production

Ces fichiers sont des sources de démonstration versionnées. Ils doivent être placés dans le stockage objet privé, jamais dans `frontend/public`. L'application doit provisionner un dossier de démonstration personnel et en lecture seule pour chaque utilisateur authentifié, tout en réutilisant ces objets communs sans autoriser leur suppression.
