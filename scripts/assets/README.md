# Modèle de DPE appartement

Le générateur remplit le **modèle national de rapport pour un appartement existant**, version applicable à partir du 1er septembre 2025, publié par le ministère chargé de la construction.

- [Page de publication officielle](https://rt-re-batiment.developpement-durable.gouv.fr/modeles-des-dpe-a788.html)
- [PDF source](https://rt-re-batiment.developpement-durable.gouv.fr/IMG/pdf/02_dpe_existant_appartement_01.09_2025.pdf), récupéré le 12 septembre 2026.
- SHA-256 : `1e6096dc06030e5696aff1046acf279dab8b827703081778366a0520c0cd4131`.

Ce PDF public porte déjà la mention « Exemple de DPE, données fictives non représentatives ». Il est conservé tel que publié. Aucune page des dossiers privés de Crozatier ou de Reuilly n'est embarquée. Ces dossiers ont servi à la comparaison visuelle.

Le script `scripts/demo_dpe.py` conserve les fonds, pictogrammes, tableaux et rubriques du ministère. Il supprime les champs du spécimen par caviardage PDF avant de les remplir, remplace les graphiques variables et retire QR code, signature, liens, annotations et métadonnées d'origine. La sortie contient huit pages avec une mention de démonstration sur chacune. Le résultat n'est pas un DPE certifié et ne provient pas d'un moteur de calcul 3CL.

Les polices IBM Plex Sans Regular et Bold complètes permettent d'insérer les nouveaux textes, notamment les euros et les accents, sans dépendre des sous-ensembles du PDF. Elles sont distribuées sous SIL Open Font License 1.1, reproduite dans `IBM-Plex-LICENSE.txt`.

- [Police Regular](https://github.com/IBM/plex/blob/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-Regular.ttf)
- [Police Bold](https://github.com/IBM/plex/blob/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-Bold.ttf)
- [Licence IBM](https://github.com/IBM/plex/blob/master/LICENSE.txt)

Les fichiers locaux rendent la génération indépendante du réseau après installation de PyMuPDF. Le contrôle d'empreinte refuse un changement de maquette sans révision des coordonnées de remplacement.
