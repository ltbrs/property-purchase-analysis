# Référentiel d’analyse immobilière Acquora

Version métier : 31 août 2026  
Périmètre : achat d’un logement existant en France, avec un focus sur les lots de copropriété. Les calendriers énergétiques cités correspondent à la France métropolitaine ; les territoires ultramarins doivent utiliser une juridiction et des dates d’effet dédiées.

## Objet

Ce référentiel décrit ce qu’Acquora devrait pouvoir extraire, calculer et rapprocher à partir des huit familles de documents du dossier acheteur. Il sert à la fois de cible produit, de spécification de normalisation et de catalogue de règles.

- [Catalogue par document](./document-analysis-catalog.md)
- [Catalogue des analyses croisées](./cross-document-analysis-catalog.md)
- [Écart avec l’implémentation actuelle et priorités](./current-gap-analysis.md)

Il s’agit d’aide à la décision. Une alerte Acquora ne doit jamais affirmer à elle seule la conformité juridique, la solidité du bâti, le coût réel d’un chantier ou l’opposabilité d’une clause.

## Vocabulaire de sortie

| Type | Signification dans le rapport | Règle d’affichage |
|---|---|---|
| `INFO` | Fait utile, sans jugement défavorable | Afficher avec sa valeur, son périmètre et sa source |
| `RASSURANT` | Conclusion explicitement favorable et suffisamment couverte | Ne jamais déduire d’un silence ou d’une absence d’extraction |
| `RISQUE` | Fait défavorable confirmé ou conséquence déterministe conditionnelle | Dire ce qui est établi, ce qui est conditionnel et pourquoi |
| `VÉRIFICATION` | Signal plausible qui exige une confirmation humaine ou un document complémentaire | Ne pas le présenter comme avéré |
| `MANQUANT` | Document ou champ attendu absent, périmètre non visité ou donnée inexploitable | Expliquer pourquoi l’information est attendue dans ce contexte |
| `INCOHÉRENCE` | Deux sources comparables se contredisent au-delà d’une tolérance définie | Montrer les deux valeurs, leurs définitions et leurs sources |

## Échelle de priorité proposée

La priorité mesure l’urgence pour l’acheteur, pas la certitude du signal.

| Niveau | Usage |
|---|---|
| `CRITIQUE` | Danger explicite, impossibilité d’usage prévue par le projet, procédure grave ou exposition financière majeure et certaine |
| `ÉLEVÉE` | Peut changer la décision d’achat, le financement ou imposer une expertise avant engagement |
| `MOYENNE` | Doit être clarifié ou chiffré avant l’acte ; impact réel mais encore incomplet |
| `FAIBLE` | Point de vigilance ou information de gestion sans urgence démontrée |
| `INFO` | KPI ou élément rassurant sans alerte |

Les montants absolus ne doivent pas, seuls, fixer la gravité. Un coût doit si possible être rapporté au lot, au prix d’achat, à la surface, au budget annuel et à la trésorerie disponible. Les seuils réglementaires restent des règles versionnées par date et contexte.

## Convention de chaque ligne

Chaque ligne des catalogues comporte :

- un code stable ;
- la sortie utilisateur attendue ;
- une condition déterministe ou un fait à extraire ;
- la nature et la priorité ;
- la méthode recommandée ;
- l’action concrète de l’acheteur et l’interlocuteur ;
- la preuve minimale à conserver.

`Règle` signifie que la décision finale est déterministe. `LLM` signifie uniquement extraction ou normalisation structurée : le modèle ne décide pas de la gravité. `Calcul` exclut l’arithmétique par LLM. `Croisement` compare des faits normalisés portant chacun leur provenance.

## Principes de décision

1. Une phrase absente n’est pas un constat rassurant.
2. Un diagnostic favorable ne rassure que sur son périmètre inspecté et à sa date.
3. Les surfaces DPE, Carrez, habitable, cadastrale et fiscale ne sont pas interchangeables.
4. Un montant collectif ne doit jamais être affiché comme quote-part du lot sans clé de répartition explicite.
5. « Voté », « discuté », « devis demandé », « en cours », « payé » et « achevé » sont des états distincts.
6. La présence d’un aléa cartographique ne prouve pas un sinistre du bâtiment ; un sinistre documenté est un signal différent.
7. L’applicabilité d’une pièce dépend du type de bien, de son âge, de sa localisation, de ses équipements et du projet de l’acheteur.
8. Une conséquence de location est affichée seulement si l’utilisateur indique un projet locatif, ou sous forme d’information conditionnelle clairement libellée.
9. Toute règle légale comporte une date d’effet et une source ; elle doit pouvoir être mise à jour sans modifier le schéma des faits.

## Sources publiques principales

Sources consultées et en vigueur ou publiées au 31 août 2026 :

- [Achat d’un logement en copropriété — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F37190)
- [Promesse de vente d’un logement existant — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F2965)
- [Diagnostic de performance énergétique — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F16096)
- [CREP / plomb — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F1142)
- [État d’amiante — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F742)
- [Termites — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F3150)
- [Diagnostic gaz — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F17337)
- [Diagnostic électricité — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F18692)
- [Assainissement — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F31685)
- [État des risques — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F12239)
- [Information acquéreur-locataire — Géorisques](https://www.georisques.gouv.fr/information-des-acquereurs-et-locataires)
- [Règlement de copropriété — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F2589)
- [Carnet d’entretien — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F2665)
- [Plan pluriannuel de travaux — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F36760)
- [Fonds de travaux — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F34026)
- [Copropriété en difficulté — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F20388)
- [Taxe foncière sur les propriétés bâties — Service Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F59)

## Hors périmètre qui reste à demander séparément

Les huit documents ne permettent pas, même parfaitement analysés, de couvrir seuls l’état réel du logement. Le rapport doit signaler les pièces contextuelles importantes : titre et projet d’acte, pré-état/état daté, fiche synthétique, état descriptif de division et modificatifs, PPPT/PPT, DTG, DPE collectif, devis et factures, contrats d’assurance et sinistres, bail en cours, urbanisme, servitudes, autorisations de travaux privatifs, audit énergétique lorsque applicable et visite technique du bien.
