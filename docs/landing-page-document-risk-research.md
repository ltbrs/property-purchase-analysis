# Risques documentaires avant un achat immobilier : sources et positionnement Acquora

## Conclusion

La recherche ne permet pas de soutenir l’affirmation « 50 % des DPE sont faux », ni de produire neuf taux comparables de documents erronés. La promesse commerciale pertinente est de **comprendre les travaux, charges, anomalies, contradictions et informations manquantes avant de s’engager**. Une pièce parfaitement exacte peut contenir une information défavorable à l’achat. À l’inverse, une incohérence documentaire ne prouve pas une fraude.

Trois données peuvent illustrer les enjeux, avec leur périmètre visible : les anomalies électriques observées à la vente par l’ONSE, l’ancienneté de certaines dates d’AG enregistrées au RNIC et l’exposition des maisons aux argiles selon Géorisques. Elles ne mesurent ni la performance d’Acquora ni la probabilité qu’un dossier donné comporte un problème.

Cette note couvre les logements existants en France, maisons et appartements, avec une attention particulière à la copropriété. Les sources ont été consultées le 12 septembre 2026. Les dates des observations restent précisées lorsqu’elles sont antérieures à cette consultation. Les recommandations marketing sont des hypothèses à mesurer, pas des résultats d’expérimentation.

## Périmètre du produit

Le catalogue actuel comporte **huit familles attendues pour un appartement en copropriété, DPE inclus**, et quatre familles communes aux maisons. Les charges, comptes et appels de fonds sont regroupés dans une même famille d’interface. Ces catégories ne constituent pas une liste réglementaire exhaustive.

Référence produit : [catalogue des documents](../frontend/features/documents/document-catalog.ts). Le nombre de PDF peut être supérieur au nombre de familles : plusieurs exercices comptables, plusieurs PV, annexes ou diagnostics séparés. Le DPE et l’état des risques peuvent aussi être fournis à l’intérieur d’un dossier de diagnostics.

Le rapport doit distinguer quatre situations : un fait défavorable explicite, une conséquence possible à confirmer, une contradiction entre pièces et une absence d’information. Les statistiques nationales ne doivent jamais remplacer les preuves propres au bien.

## Fiabilité du DPE

Le Focus n° 105 du Conseil d’analyse économique examine les concentrations de DPE du côté favorable des seuils de classes. Il estime à **1,7 %** la part de l’ensemble des DPE après la réforme de 2021 soupçonnés de manipulation aux seuils. Ce résultat ne mesure pas toutes les erreurs possibles, et ne permet pas d’identifier avec certitude un diagnostic frauduleux. La publication donne également 13 % au voisinage des seuils, un autre dénominateur qu’il faut impérativement conserver.[^1]

La Cour des comptes reprend le 1,7 % pour juillet 2021 à décembre 2023 dans son rapport de juin 2025. Elle souligne aussi les limites des tests de consommateurs sur de petits échantillons. Les tableaux de contrôle DGCCRF recensent **316 établissements avec anomalie sur 457 contrôlés en 2023, soit 69,2 %**. Ces contrôles portent sur les pratiques professionnelles et commerciales, auprès d’opérateurs ciblés. Ce n’est pas un taux de DPE inexacts.[^2]

Une divergence mérite d’être conservée dans le dossier de sources : le Focus CAE accessible indique **3,2 % avant 2021** à sa page 5, tandis que la Cour reprend **3,9 %** à sa page 91. Sans explication établie de cet écart, aucune comparaison historique chiffrée n’est retenue dans la landing page. Le chiffre commun de 1,7 % reste une estimation historique, pas un indicateur de qualité des DPE établis en 2026.[^1][^2]

L’affirmation « 50 % des DPE sont faux » est donc écartée. Un écart entre facture réelle et consommation conventionnelle n’est pas non plus une démonstration suffisante : ces indicateurs ne décrivent pas le même usage du logement. La lecture des documents n’équivaut pas à une nouvelle mesure sur place.

**Décision éditoriale :** expliquer les limites de la vérification du DPE dans la FAQ, sans faire de la détection de fraude la promesse principale.

## Électricité : une donnée récente et directement liée à la vente

Le baromètre ONSE 2025, fondé sur une analyse Diagamter, distingue **84,6 % d’installations présentant au moins une anomalie parmi 320 000 diagnostics de vente** et 74 % parmi 80 000 diagnostics de location. Il concerne des installations de plus de 15 ans. La valeur globale de 82,6 % mélange les deux populations.[^3]

Pour Acquora, le sous-ensemble vente est le plus pertinent. Il remplace le 83 % du baromètre 2024. L’ONSE est un observatoire de filière, pas un service statistique ministériel. Le corpus d’un opérateur ne doit pas être présenté comme un tirage aléatoire de toutes les ventes françaises. Une anomalie n’est pas systématiquement un danger immédiat ni un devis de rénovation.

Formulation retenue : « 84,6 % des installations électriques de plus de 15 ans étudiées à la vente présentent une anomalie », avec taille du corpus, opérateur, édition et lien vers la page 2. **Le chiffre mesure les installations examinées, pas les erreurs de diagnostic.**

## Copropriété : l’ancienneté des informations est un problème en soi

Le Sénat constate en 2024 une date de dernière AG approuvant les comptes vieille de plus de deux ans pour **90 000 copropriétés parmi 438 000 ayant renseigné cette date**. Le rapport précise que l’estimation dépend de la qualité des informations du RNIC. La référence correcte est la **page imprimée 28, également page 28 du PDF**, et non la page 27 indiquée précédemment.[^4]

Une donnée ancienne dans le registre peut refléter une absence de mise à jour. Elle ne prouve donc pas qu’aucune AG ne s’est tenue, qu’un PV est faux ou qu’un immeuble est insolvable. La landing conserve la formulation « date d’AG », son dénominateur et cette réserve.

Les données ANIL apportent un autre éclairage : parmi 41 655 consultations copropriété en 2018, 17,3 % concernaient les travaux, 14,1 % les charges ou impayés et 6,7 % le règlement. Elles décrivent des besoins de conseil, pas la fréquence des problèmes chez tous les acquéreurs. Elles confortent qualitativement les thèmes éditoriaux, sans devenir des chiffres de conversion.[^5]

**Décision éditoriale :** montrer une question concrète sur des travaux évoqués mais non chiffrés. Distinguer explicitement une demande de devis, un vote et une somme effectivement imputable à l’acquéreur.

## Risques naturels : actualiser la carte, conserver les unités

Géorisques indique que la carte actualisée en 2026 couvre **12,1 millions de maisons** en zone moyenne ou forte d’exposition au retrait-gonflement des argiles. Le dossier expert donne 61,5 % des maisons ; l’Observatoire national des risques naturels arrondit à 62 %. Les 55 % également cités concernent la **surface du territoire**, pas les maisons.[^6][^7]

Le chiffre de 54 % repris du SDES dans la première recherche correspondait à une cartographie antérieure. Il ne doit pas être présenté comme l’état courant en septembre 2026. La page retient le nombre de maisons, qui évite la confusion entre pourcentages et leurs arrondis.

L’exposition ne signifie pas qu’une maison présente des fissures. Acquora peut aider à lire un état des risques fourni ; la landing ne promet pas une interrogation automatique de Géorisques ni une expertise géotechnique. Une vérification à l’adresse et sur la cartographie actuelle reste distincte de la lecture du PDF.

**Décision éditoriale :** employer cette donnée pour rappeler que la visite ne suffit pas à apprécier tous les risques, avec le lien de source directement accessible.

## Résultats pour les huit familles Acquora

« Non trouvé » signifie qu’aucun indicateur national suffisamment étayé n’a été identifié dans les sources consultées. Ce n’est ni une preuve d’absence d’erreurs ni un recensement exhaustif de toutes les publications.

| Famille | Taux de documents erronés | Donnée ou source pertinente | Utilité pour l’acheteur | Décision landing |
|---|---|---|---|---|
| DPE | Estimation partielle de manipulations aux seuils, pas de toutes les erreurs | CAE, Cour des comptes [1, 2] | Comprendre les données et repérer des divergences apparentes | FAQ sur les limites, aucun taux d’erreur promis |
| Diagnostics techniques | Non trouvé par diagnostic | ONSE 2025 pour l’état électrique [3] | Lire anomalies, réserves et parties non visitées | Chiffre vente avec périmètre |
| État des risques | Non trouvé | Cartographie Géorisques 2026 [6, 7] | Vérifier exposition mentionnée, adresse et date | Nombre de maisons exposées, sans diagnostic individuel |
| Taxe foncière | Pas de taux d’erreur des avis remis à la vente | Rapport parlementaire sur les erreurs d’attribution [8] | Relire année, bien concerné et montant | Description du budget, sans statistique accrocheuse |
| PV d’AG | Non trouvé | Dates renseignées au RNIC, Sénat [4] | Retrouver travaux, décisions et suites d’une AG à l’autre | Date d’AG avec réserve déclarative |
| Charges et comptes | Non trouvé | Consultations ADIL [5] | Distinguer budget, dépenses, provisions et impayés | Exemple de montants à rapprocher |
| Règlement de copropriété | Non trouvé | ANIL et pièces de vente, Service Public [5, 9] | Comprendre lot, destination, restrictions et modificatifs | Famille visible dans la liste des documents |
| Carnet d’entretien | Non trouvé | Pièces de vente, Service Public [9] | Lire historique et entretien des équipements | Exemple d’une pièce à demander |

Le rapport parlementaire sur les impôts locaux mentionne en moyenne **394 391 dossiers annuels** de dégrèvement pour erreur d’attribution entre 2017 et 2024, environ 1,2 % des contribuables concernés. En 2024, il indique 134 642 dossiers. L’erreur d’attribution correspond à un avis envoyé au mauvais contribuable ; elle ne mesure pas les erreurs de montant des avis fournis aux acheteurs. Cette donnée reste en recherche, hors landing.[^8]

L’étude ministérielle de 2019 sur les contentieux de copropriété compte près de 28 700 demandes en paiement des charges en 2017, contre 22 300 en 2007. Ce volume historique de contentieux n’est ni une proportion de comptabilités erronées ni un indicateur actuel. Il n’est pas retenu en accroche.[^10]

## Diagnostics susceptibles d’être compris comme les « huit autres documents »

Les diagnostics regroupés avec le DPE varient selon le logement. Les sources publiques décrivent des obligations, des expositions ou des anomalies physiques. Elles ne fournissent pas un même dispositif de contre-expertise permettant de comparer leur taux d’erreur.[^11]

| Diagnostic ou information | Résultat de la recherche | Conséquence éditoriale |
|---|---|---|
| Plomb, CREP | Service Public décrit le diagnostic et Santé publique France la surveillance du saturnisme. Aucun taux national de CREP erronés identifié [12, 13] | Ne pas transformer des cas sanitaires en probabilité de rapport faux |
| Amiante | Le Sénat documentait les limites du repérage en 2005, puis en 2014. Sources historiques qualitatives [14] | Ne pas en déduire un taux de faux négatifs en 2026 |
| Termites | Le ministère décrit les zones et modalités du diagnostic, sans série nationale d’erreurs identifiée [11] | Parler de conclusions, localisation et périmètre inspecté |
| Gaz | Le ministère cite 98 % des accidents, fuites et explosions dans les installations intérieures, sans millésime statistique suffisamment explicite pour une accroche actuelle [11] | Exclure ce chiffre de la landing ; ce n’est pas un taux de diagnostics faux |
| Électricité | Anomalies d’installations documentées par l’ONSE, pas taux de rapports incorrects [3] | Utilisable avec les limites exposées plus haut |
| État des risques | Données d’exposition Géorisques, pas audit national des formulaires [6, 7] | Ne pas confondre zone exposée et sinistre avéré |
| Assainissement non collectif | Eaufrance publie 63 % de dispositifs conformes en 2024 [15] | Ne pas transformer le complément en 37 % de rapports erronés ou en devis automatique |
| Bruit des aérodromes | Service Public décrit l’information liée aux plans d’exposition, sans taux d’erreur identifié [16] | Lire localisation et zone ; ne pas inventer de fréquence nationale |
| Mérule | Information contextuelle décrite parmi les diagnostics et informations immobilières [11] | Ne pas promettre la détection d’un champignon absent des pièces |

Pour l’assainissement, l’indicateur SISPEA et son périmètre doivent être examinés avant tout usage commercial plus précis. La conformité d’un dispositif constitue une observation technique ; le rapport peut parfaitement décrire un dispositif non conforme.[^15]

## Ce que la landing doit faire comprendre

La première visite donne envie d’acheter. Les pièces permettent de poser des questions sur les dépenses, l’état du bien et la copropriété. Acquora doit relier ces deux moments avec un bénéfice précis : rendre les points documentés plus faciles à trouver et à discuter.

L’ordre proposé est : promesse acheteur, préoccupations concrètes, exemple de rapport, chiffres de contexte, familles de documents, fonctionnement, objections et création de dossier. L’exemple arrive avant les statistiques pour montrer la valeur réelle du service. Les institutions sont citées comme sources, sans logos suggérant une validation d’Acquora.

Les formulations suivantes sont exclues : garantie d’absence de risque, détection certaine de fraude, économies moyennes sans données clients, délais d’analyse non mesurés, avis ou clients inventés. Un exemple fictif doit être identifié visiblement. Ses pages ne doivent jamais passer pour des citations de documents réellement fournis.

Pour chaque constat, la bonne articulation est : **ce que dit la pièce, pourquoi cela mérite attention, ce qui reste inconnu, puis la question à poser**. Une somme de travaux d’immeuble ne devient pas une charge personnelle sans clé de répartition et contexte de paiement. Deux montants différents ne sont contradictoires qu’après vérification de leur périmètre.

## Limites et mise à jour

Le corpus contient des publications institutionnelles, une étude économique et un baromètre professionnel. Leur autorité ne rend pas leurs populations interchangeables. Les échantillons ciblés, les déclarations de registre et les données historiques conservent leurs limites même lorsqu’un organisme public les reprend.

L’absence de taux national par document interdit une promesse chiffrée générale sur les « dossiers faux ». Elle laisse une proposition utile : aider l’acheteur à comprendre les éléments réellement présents, les pièces absentes et les contradictions possibles.

Les statistiques choisies sont du contexte. Une hausse de conversion, une baisse des mauvaises décisions ou une fiabilité accrue d’Acquora doivent être établies séparément. Le plan d’acquisition, de mesure et les choix d’implémentation figurent dans [la stratégie SEO et conversion](landing-page-seo-conversion-strategy.md).

## Sources

[^1]: Conseil d’analyse économique, [Les effets des réformes du diagnostic de performance énergétique sur sa fiabilité, Focus n° 105](https://cae-eco.fr/static/pdf/focus-105-fiabilite-dpe-240626.pdf), juin 2024, notamment pages PDF 1 et 5. Étude économétrique des distributions aux seuils.
[^2]: Cour des comptes, [La mise en œuvre du diagnostic de performance énergétique](https://www.ccomptes.fr/sites/default/files/2025-06/20250603-Mise-en-oeuvre-diagnostic-performance-energetique.pdf), juin 2025, notamment pages 39, 90, 91 et 94. La page 91 porte la synthèse de l’étude CAE ; la page 94 contient les contrôles DGCCRF.
[^3]: Observatoire national de la sécurité électrique, [Baromètre 2025](https://www.onse.fr/wp-content/uploads/2025/05/Barometre-ONSE-2025_020525.pdf), édition 2025, pages PDF 1 et 2, analyse Diagamter. La page 2 sépare vente et location.
[^4]: Sénat, commission d’enquête, [La paupérisation des copropriétés immobilières](https://www.senat.fr/rap/r23-736-1/r23-736-11.pdf#page=28), rapport n° 736, juillet 2024, page 28, note 5 pour le dénominateur et la réserve RNIC.
[^5]: ANIL, [Réforme du droit de la copropriété : remarques du réseau ANIL-ADIL](https://www.anil.org/etudes-reforme-droit-copropriete-reseau-anil-adil/), février 2020, consultations de 2018.
[^6]: Géorisques, [Dossier expert sur le retrait-gonflement des argiles](https://www.georisques.gouv.fr/consulter-les-dossiers-thematiques/retrait-gonflement-des-argiles), cartographie actualisée en 2026, rubrique sur les 12 millions de maisons exposées.
[^7]: Géorisques, [Observatoire national des risques naturels](https://www.georisques.gouv.fr/observatoire-national-des-risques-naturels), indicateurs d’exposition RGA 2026. Arrondi à 62 % à distinguer du 61,5 % du dossier expert et des 55 % de surface territoriale.
[^8]: Assemblée nationale, [Rapport d’information sur les dysfonctionnements dans la gestion des impôts locaux](https://www.assemblee-nationale.fr/dyn/opendata/RINFANR5L17B1594.html), n° 1594, 18 juin 2025, partie sur les erreurs d’attribution.
[^9]: Service Public, [Achat d’un logement en copropriété](https://www.service-public.gouv.fr/particuliers/vosdroits/F37190), fiche en vigueur consultée le 12 septembre 2026, documents remis lors de la vente.
[^10]: Ministère de la Justice, [Les contentieux de la copropriété](https://www.dalloz-actualite.fr/sites/dalloz-actualite.fr/files/resources/2019/02/dacsmjcontentieuxcopro.pdf), étude de 2019 sur 2007 à 2017, copie de la publication ministérielle hébergée par Dalloz. Source historique exclue des accroches.
[^11]: Ministère chargé du logement, [Diagnostics techniques immobiliers](https://www.ecologie.gouv.fr/politiques-publiques/diagnostics-techniques-immobiliers), page consultée le 12 septembre 2026, rubriques par diagnostic. La présence d’une règle sur cette page n’établit pas son implémentation dans Acquora.
[^12]: Service Public, [Constat de risque d’exposition au plomb](https://www.service-public.gouv.fr/particuliers/vosdroits/F1142), fiche consultée le 12 septembre 2026.
[^13]: Santé publique France, [Surveillance du saturnisme infantile en Occitanie](https://www.santepubliquefrance.fr/content/download/730036/4702772?version=1), bulletin du 13 juin 2025. Surveillance sanitaire distincte d’une évaluation de la fiabilité des CREP.
[^14]: Sénat, [Amiante : des enjeux toujours actuels, relever le défi du désamiantage](https://www.senat.fr/notice-rapport/2013/r13-668-notice.html), rapport n° 668, 2014 ; antécédent : [rapport sur le drame de l’amiante](https://www.senat.fr/rap/r05-037-1/r05-037-1.html), 26 octobre 2005.
[^15]: Eaufrance, [Part des dispositifs d’assainissement non collectif conformes en 2024](https://www.eaufrance.fr/chiffres-cles/part-des-dispositifs-dassainissement-non-collectif-conformes-en-2024), indicateur 2024 fondé sur SISPEA, consulté le 12 septembre 2026.
[^16]: Service Public, [Diagnostic Bruit des aéroports](https://www.service-public.gouv.fr/particuliers/vosdroits/F35266), vérifié le 20 août 2026.
