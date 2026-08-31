# Catalogue des analyses croisées

Une analyse croisée ne compare que des faits normalisés avec un périmètre explicite. Elle conserve toutes les sources qui participent au raisonnement. Les tolérances proposées sont des points de départ à calibrer sur le golden dataset, pas des vérités métier universelles.

## A. Identité, périmètre et complétude

| Code | Documents comparés | Condition / résultat | Type · priorité | Méthode | Action acheteur | Preuve minimale |
|---|---|---|---|---|---|---|
| `X_PROPERTY_IDENTITY_MISMATCH` | Tous | Adresse, commune, bâtiment, étage ou porte incompatibles après normalisation | INCOHÉRENCE · ÉLEVÉE | Identités + géocodage | Isoler la pièce erronée et demander une version portant sur le bon bien au vendeur/notaire | Identités contradictoires |
| `X_LOT_ID_MISMATCH` | Règlement/EDD, Carrez, charges, AG, acte si fourni | Numéro ou composition du lot diverge | INCOHÉRENCE · ÉLEVÉE | Graphe des lots | Faire confirmer la consistance exacte par le notaire avant engagement | Désignations de lots |
| `X_ANNEX_MISSING_FROM_TITLE_SET` | Annonce/visite, EDD, Carrez, taxe, charges | Cave, parking, jardin, grenier ou chambre annoncé mais absent des pièces juridiques | VÉRIFICATION · ÉLEVÉE | Rapprochement d’entités | Exiger titre/EDD/modificatif prouvant le droit transmis | Annexe annoncée et pièces absentes |
| `X_DOCUMENT_DATE_CONFLICT` | Deux versions du même document | Même identifiant mais dates, conclusions ou montants incompatibles | INCOHÉRENCE · ÉLEVÉE | Versionnage | Demander la version définitive et conserver l’historique | Deux versions complètes |
| `X_NEWER_DOCUMENT_MISSING` | AG, comptes, taxe, ERP, DPE, diagnostics | Une autre pièce cite une mise à jour/AG/diagnostic plus récent non fourni | MANQUANT · ÉLEVÉE | Références croisées | Demander expressément le document cité | Citation et liste des pièces |
| `X_WRONG_PROPERTY_TYPE` | Règlement/EDD, contexte utilisateur, documents | Bien traité comme maison alors qu’il est en copropriété, ou inversement | INCOHÉRENCE · CRITIQUE | Règle de contexte | Corriger le type de dossier avant de recalculer pièces attendues et risques | Faits établissant le régime |
| `X_APPLICABILITY_MATRIX_GAP` | Dates bâtiment, équipements, localisation, DDT | Un déclencheur prouve qu’un diagnostic/pièce devrait être vérifié mais aucun document n’est exploitable | MANQUANT · ÉLEVÉE | Moteur d’applicabilité daté | Faire confirmer la liste des pièces par le notaire et demander les manquantes | Déclencheur et absence |
| `X_PAGE_CITATION_CONFLICT` | Fait extrait et page source | La citation ne supporte pas la valeur, l’unité ou le statut affiché | INCOHÉRENCE · ÉLEVÉE | Validation de provenance | Masquer le fait et relancer l’extraction ou demander le PDF original | Fait, citation et texte page |

## B. Surfaces, lots et usages

| Code | Documents comparés | Condition / résultat | Type · priorité | Méthode | Action acheteur | Preuve minimale |
|---|---|---|---|---|---|---|
| `X_SURFACE_DPE_CARREZ_GAP` | DPE, Carrez | Écart au-delà du maximum de 1 m² ou 2 %, présenté avec les définitions différentes | VÉRIFICATION · MOYENNE | Calcul | Demander au diagnostiqueur/notaire d’expliquer le périmètre ; remesurer si décisif | Deux surfaces et définitions |
| `X_SURFACE_WITH_ANNEXES` | Carrez, EDD | Les lots inclus/exclus du mesurage ne correspondent pas à la vente | INCOHÉRENCE · ÉLEVÉE | Graphe des lots | Demander une attestation corrigée ou complète avant signature | Détail Carrez et EDD |
| `X_SURFACE_TAX_NOT_COMPARABLE` | Taxe, DPE, Carrez | Une surface fiscale/cadastrale est présentée comme surface Carrez ou habitable | VÉRIFICATION · MOYENNE | Typage strict | Demander la fiche d’évaluation cadastrale ; ne pas signaler un écart brut comme erreur | Valeurs et libellés |
| `X_DESTINATION_ACTUAL_USE_CONFLICT` | Règlement, EDD, AG/autorisations, DPE/DDT | Usage observé/documenté incompatible avec destination du lot et aucune autorisation | RISQUE · ÉLEVÉE | Contexte + rapprochement | Faire vérifier la régularité par le notaire et demander autorisations au vendeur | Clause, usage et absence d’autorisation |
| `X_BUYER_PROJECT_NOT_ALLOWED` | Projet acheteur, règlement, DPE, mairie si donnée | Location, meublé touristique, profession, commerce, division ou travaux incompatibles | RISQUE · CRITIQUE | Moteur de contexte | Obtenir validation écrite du notaire/mairie et prévoir une condition suspensive si central | Projet et règles applicables |
| `X_PRIVATE_COMMON_SCOPE_CONFLICT` | Règlement, DPE, AG, carnet | Un travail recommandé comme individuel porte en réalité sur une partie commune, ou inversement | VÉRIFICATION · ÉLEVÉE | Ontologie des composants | Faire confirmer la responsabilité et l’autorisation par syndic/notaire avant devis | Composant et clauses |

## C. Énergie, équipements et diagnostics

| Code | Documents comparés | Condition / résultat | Type · priorité | Méthode | Action acheteur | Preuve minimale |
|---|---|---|---|---|---|---|
| `X_HEATING_TYPE_CONFLICT` | DPE, charges, règlement, AG, carnet | Énergie ou caractère individuel/collectif contradictoire | INCOHÉRENCE · ÉLEVÉE | Taxonomie équipements | Vérifier l’installation à la visite et demander contrat/facture au syndic | Champs contradictoires |
| `X_HEATING_COST_NOT_IN_BUDGET` | DPE, charges | DPE dit collectif mais aucune charge de chauffage identifiable, ou individuel mais poste collectif facturé sans explication | VÉRIFICATION · MOYENNE | Rapprochement poste | Demander le mode de comptage et la clé de charges au syndic | Type DPE et comptes |
| `X_ENERGY_COST_VS_ACTUAL_BILLS` | DPE, charges/factures si présentes | Dépenses conventionnelles très différentes des dépenses réelles, après normalisation de période et périmètre | VÉRIFICATION · MOYENNE | Calcul | Examiner occupation, météo, consigne et énergie incluse ; ne pas déclarer le DPE faux automatiquement | Fourchette, factures et hypothèses |
| `X_DPE_RECOMMENDATION_BLOCKED` | DPE, règlement, AG | Recommandation majeure exige une décision collective déjà refusée, ou est interdite sans autorisation | RISQUE · ÉLEVÉE | Composants + timeline | Faire chiffrer une alternative réalisable et interroger le syndic | Recommandation et décision/clause |
| `X_DPE_RECOMMENDATION_IN_PPT` | DPE, PPPT/PPT, AG, carnet | Même rénovation prévue collectivement avec calendrier et coût | INFO ou RISQUE | Rapprochement projet | Utiliser le plan collectif et sa quote-part plutôt qu’un devis individuel isolé | Deux descriptions et calendrier |
| `X_DPE_AFTER_ENERGY_WORKS` | DPE, carnet, AG | DPE antérieur à des travaux énergétiques substantiels achevés | VÉRIFICATION · MOYENNE | Dates + composants | Demander un DPE mis à jour ou attestation permettant d’évaluer le bien après travaux | Date DPE et réception travaux |
| `X_DPE_IGNORES_RECENT_SYSTEM` | DPE, carnet, AG, visite | Système décrit remplacé avant la date du DPE ou équipement actuel absent du rapport | INCOHÉRENCE · ÉLEVÉE | Timeline | Faire clarifier par le diagnostiqueur et demander correction/nouveau DPE | Dates et équipements |
| `X_DIAGNOSTIC_DEFECT_WORKS_PLANNED` | DDT, AG, carnet, appels | Une anomalie a un chantier voté/planifié correspondant | INFO ou RISQUE | Rapprochement composant | Vérifier que le chantier couvre bien le défaut, son financement et son achèvement | Anomalie et résolution |
| `X_DIAGNOSTIC_DEFECT_UNADDRESSED` | DDT, AG, carnet | Danger/anomalie ancien sans correction ni suivi retrouvé | RISQUE · ÉLEVÉE | Timeline | Exiger preuve de correction ou devis et expertise adaptée | Constat initial et absence de suivi |
| `X_ASBESTOS_PLANNED_WORK_COST` | Amiante, DPE, AG/PPT, carnet | Travaux prévus touchent un matériau/une zone amiantée | RISQUE · CRITIQUE à ÉLEVÉE | Croisement zones/composants | Faire intégrer repérage avant travaux, désamiantage et délais au budget par des professionnels | Localisation amiante et chantier |
| `X_LEAD_PLANNED_WORK_OR_OCCUPANCY` | CREP, travaux, projet familial | Revêtement dégradé concerné par travaux ou occupation sensible | RISQUE · CRITIQUE | Zones + contexte | Sécuriser et chiffrer avec professionnel ; demander avis sanitaire si rapport le prévoit | Mesure, état, zone et contexte |
| `X_GAS_ELECTRIC_FIX_CLAIMED` | Diagnostic, factures/carnet/AG | Le vendeur affirme une correction mais aucune attestation/facture postérieure ne la prouve | MANQUANT · ÉLEVÉE | Timeline | Demander facture et contrôle post-travaux avant usage | Anomalie et preuve manquante |
| `X_VENTILATION_HUMIDITY_PATTERN` | DPE, diagnostics, AG, carnet | Ventilation insuffisante et infiltrations/moisissures/humidité récurrentes | RISQUE · ÉLEVÉE | Graphe causal prudent | Mandater un spécialiste bâtiment/ventilation ; ne pas attribuer une cause unique automatiquement | Signaux indépendants sourcés |
| `X_SUMMER_COMFORT_RULES_CONSTRAINT` | DPE, règlement, AG | Mauvais confort d’été mais protections/climatisation soumises à contraintes de façade | RISQUE · MOYENNE | Contexte | Vérifier solutions autorisées et coût avec syndic/thermicien | DPE et clause/résolution |

## D. Risques naturels, sinistres et bâtiment

| Code | Documents comparés | Condition / résultat | Type · priorité | Méthode | Action acheteur | Preuve minimale |
|---|---|---|---|---|---|---|
| `X_ERP_VS_ADDRESS` | ERP, taxe, DPE, règlement | Parcelle/adresse ERP ne correspond pas au bien | INCOHÉRENCE · ÉLEVÉE | Géocodage | Régénérer l’ERP sur la bonne parcelle | Identités géographiques |
| `X_HAZARD_WITH_MATCHING_DAMAGE` | ERP, AG, carnet, diagnostics | Aléa cartographié et désordre/sinistre de même nature documenté | RISQUE · CRITIQUE à ÉLEVÉE | Taxonomie aléa-dommage | Mandater expert indépendant, demander assurance et historique des réparations | Aléa et dommage distincts |
| `X_COMPENSATED_DISASTER_MISSING_FROM_ERP` | AG/carnet/assurance, ERP | Sinistre CatNat/CatTech indemnisé cité ailleurs mais non déclaré dans l’ERP | INCOHÉRENCE · CRITIQUE | Timeline + taxonomie | Faire rectifier l’état des risques par le vendeur/notaire | Sinistre et déclaration ERP |
| `X_DISASTER_REPAIRS_UNVERIFIED` | ERP, carnet, AG, factures | Sinistre déclaré mais achèvement/efficacité des réparations non prouvé | MANQUANT · ÉLEVÉE | Timeline | Demander expertise, réception, factures et garantie | Sinistre et pièces absentes |
| `X_FLOOD_BASEMENT_OR_GROUND_FLOOR` | ERP, EDD, Carrez, AG | Lot/annexe en sous-sol ou RDC et exposition inondation/submersion documentée | RISQUE · ÉLEVÉE | Géométrie + contexte | Visiter caves/parking, demander historique et conditions d’assurance | Niveau du lot et aléa |
| `X_GROUND_RISK_WITH_CRACKS` | ERP, AG, carnet, diagnostic | Argiles, cavités ou mouvement de terrain plus fissures/structure | RISQUE · CRITIQUE | Rapprochement prudent | Mandater expert structure/géotechnicien avant achat | Aléa et fissures sourcés |
| `X_AIRPORT_NOISE_WITH_WEAK_ENVELOPE` | Bruit/ERP, DPE | Zone de bruit et fenêtres/isolation acoustique faibles ou anciennes explicitement décrites | RISQUE · MOYENNE | Composants | Visiter aux heures de trafic et obtenir devis acoustique/aides possibles | Zone et enveloppe |
| `X_MAINTENANCE_CLAIM_CONFLICT` | Carnet, AG | Carnet dit chantier achevé mais AG ultérieure signale défaut, réserve ou reprise | INCOHÉRENCE · ÉLEVÉE | Timeline | Demander PV de réception, levée de réserves et expertise | Deux statuts datés |

## E. Travaux, appels de fonds et exposition acheteur

| Code | Documents comparés | Condition / résultat | Type · priorité | Méthode | Action acheteur | Preuve minimale |
|---|---|---|---|---|---|---|
| `X_WORK_PROJECT_TIMELINE` | AG, appels, comptes, carnet | Chronologie consolidée : discuté, voté, appelé, payé, démarré, réceptionné, garanti | INFO | Entity resolution + dates | Examiner tout état manquant avant de conclure qu’un chantier est soldé | Événements et sources |
| `X_VOTED_WORK_NO_FUNDING_CALL` | AG, appels/comptes | Travaux votés sans appel rapproché ; peut être futur, inclus ailleurs ou document absent | MANQUANT · ÉLEVÉE | Rapprochement projet | Demander échéancier et quote-part au syndic/notaire | Résolution et recherche des appels |
| `X_FUNDING_CALL_NO_AG_VOTE` | Appels/comptes, AG | Appel travaux sans résolution correspondante, hors urgence explicitement documentée | INCOHÉRENCE · ÉLEVÉE | Rapprochement projet | Demander résolution, base de l’appel et justificatif d’urgence | Appel et PV disponibles |
| `X_WORK_COST_CHANGED` | PV successifs, devis, appels, comptes | Coût d’un même projet augmente ou diminue ; version/périmètre comparables | RISQUE ou INFO | Entity resolution + calcul | Obtenir devis final et cause de variation ; recalculer la quote-part | Montants, dates et périmètres |
| `X_WORK_SHARE_RECONCILIATION` | Coût collectif, règlement, appel | Quote-part recalculée avec la clé pertinente diffère de l’appel au-delà des arrondis | INCOHÉRENCE · ÉLEVÉE | Calcul déterministe | Demander au syndic la clé et le calcul détaillé | Coût, clé, lot et appel |
| `X_WORK_BUYER_EXPOSURE` | Appels futurs, acte/date prévue, état daté | Somme des échéances explicitement rattachées au lot après la vente, sans décider seul qui paiera contractuellement | RISQUE · selon montant relatif | Calcul | Négocier la répartition dans l’acte avec le notaire et réserver la somme au financement | Échéances, lot et date de vente |
| `X_WORKS_FUND_COVERAGE` | Fonds travaux, PPT/AG, appels | Fonds mobilisable comparé aux travaux et à la part du lot | INFO ou RISQUE | Calcul | Demander le plan de financement net du fonds | Solde, affectation et travaux |
| `X_PPT_NO_FINANCING` | PPT, AG, fonds, comptes | Travaux importants planifiés mais aucun financement ou calendrier d’appels identifiable | RISQUE · ÉLEVÉE | Rapprochement | Anticiper des appels et demander simulation de quote-part au syndic | PPT et absence de financement |
| `X_REJECTED_WORK_THEN_DAMAGE` | AG successives, carnet, sinistres | Travaux rejetés/reportés suivis d’une aggravation ou d’un sinistre correspondant | RISQUE · CRITIQUE à ÉLEVÉE | Timeline | Mandater un expert et demander le nouveau plan d’action/coût | Décisions et dommage |
| `X_COMPLETED_WORK_STILL_BILLED` | Carnet/AG, appels/comptes | Appels postérieurs à l’achèvement sans échéancier ou solde explicatif | VÉRIFICATION · MOYENNE | Timeline | Demander décompte définitif et justification au syndic | Réception et appel |
| `X_WARRANTY_STILL_ACTIVE` | Carnet, factures, AG | Désordre lié à un chantier récent potentiellement encore sous garantie/assurance | VÉRIFICATION · ÉLEVÉE | Dates + composant | Demander déclaration de sinistre et activation des garanties au syndic | Réception, police et désordre |

## F. Santé financière de la copropriété

| Code | Documents comparés | Condition / résultat | Type · priorité | Méthode | Action acheteur | Preuve minimale |
|---|---|---|---|---|---|---|
| `X_ACCOUNTS_APPROVAL_CONFLICT` | PV, comptes | Comptes marqués approuvés dans une source et rejetés/ajournés dans l’autre | INCOHÉRENCE · ÉLEVÉE | Période + statut | Demander les comptes définitifs et le PV complet au syndic | Deux statuts |
| `X_ANNUAL_CHARGES_CONFLICT` | Pré-état daté, compte lot, appels, PV | Montants différents pour même lot, période et périmètre | INCOHÉRENCE · ÉLEVÉE | Typage + calcul | Faire réconcilier par le syndic avant budget final | Valeurs et périmètres |
| `X_ARREARS_TREND` | Comptes successifs, PV, fiche synthétique si fournie | Impayés en hausse/baisse en montant, ratio et nombre de débiteurs | RISQUE ou RASSURANT | Calcul temporel | Si hausse, demander recouvrement et trésorerie ; si baisse, vérifier qu’elle n’est pas un abandon de créance | Séries comparables |
| `X_ALERT_PROCEDURE_MISSING` | Ratio impayés, PV, procédures | Seuil légal potentiellement atteint sans mention de saisine, après vérification des bases exactes | VÉRIFICATION · CRITIQUE | Calcul versionné | Interroger syndic/notaire sur mandataire ad hoc et pièces judiciaires | Calcul et PV disponibles |
| `X_SUPPLIER_DEBT_SERVICE_RISK` | Comptes, AG, carnet/contrats | Dette envers prestataire essentiel avec menace de suspension ou entretien expiré | RISQUE · CRITIQUE | Rapprochement fournisseur | Demander plan de paiement et continuité de service au syndic | Dette, contrat et service |
| `X_BUDGET_UNDERSPEND_DUE_TO_MAINTENANCE_DEFERRAL` | Budgets/comptes, carnet, AG | Faibles dépenses apparentes mais entretien reporté ou contrats interrompus | RISQUE · ÉLEVÉE | Graphe d’explication | Ne pas classer les faibles charges comme rassurantes ; chiffrer le rattrapage | Comptes et reports |
| `X_HIGH_CHARGES_EXPLAINED_BY_SERVICES` | Charges, règlement, équipements | Charges élevées expliquées par chauffage, gardien, ascenseur, espaces ou travaux | INFO | Ventilation + contexte | Décider si ces services ont de la valeur pour le projet et budgéter leur tendance | Postes et services |
| `X_SELLER_DEBT_VS_GLOBAL_ARREARS` | Compte vendeur, état global | Dette du vendeur confondue avec impayés de la copropriété ou inversement | INCOHÉRENCE · ÉLEVÉE | Typage strict | Faire traiter la dette vendeur par le notaire et évaluer séparément le risque collectif | Deux périmètres financiers |
| `X_COLLECTIVE_LOAN_LOT_EXPOSURE` | AG, compte, état daté, appels | Emprunt collectif cité mais rattachement, capital restant ou échéances du lot incomplets | MANQUANT · ÉLEVÉE | Rapprochement dette | Obtenir du syndic/notaire le tableau d’amortissement et le sort à la mutation | Prêt et données manquantes |

## G. Synthèse de décision et questions générées

| Code | Documents comparés | Condition / résultat | Type · priorité | Méthode | Action acheteur | Preuve minimale |
|---|---|---|---|---|---|---|
| `X_CONFIRMED_UPCOMING_COSTS` | Tous montants lot | Somme par date des coûts futurs explicitement rattachés au lot, sans double compte | INFO/RISQUE | Calcul + déduplication | Réserver ces montants dans le financement et les faire confirmer par l’état daté | Détail de chaque composante |
| `X_POTENTIAL_UNQUANTIFIED_COSTS` | Risques/travaux sans quote-part | Liste séparée des postes probables mais non chiffrables | VÉRIFICATION · ÉLEVÉE | Agrégation typée | Demander devis/quote-part ; ne jamais les inclure comme montants certains | Signaux et absence de montant |
| `X_DUPLICATE_COST_PREVENTION` | AG, appels, comptes, PPT | Même dépense présente dans plusieurs documents | INFO interne | Entity resolution | Afficher une seule exposition avec toutes les sources | Identifiant projet et occurrences |
| `X_CONFLICT_BLOCKS_CONCLUSION` | Toute paire critique | Contradiction empêche de calculer coût, validité, usage ou danger | MANQUANT/INCOHÉRENCE · ÉLEVÉE | Règle | Suspendre la conclusion concernée et générer une question ciblée au bon interlocuteur | Faits en conflit |
| `X_REASSURING_REQUIRES_COVERAGE` | Tous | Absence de risque seulement si document récent, complet, applicable et conclusion explicitement favorable | RASSURANT · INFO | Règle de couverture | Conserver la portée et la date dans le libellé rassurant | Conclusion et périmètre |
| `X_BUYER_QUESTION` | Tous | Chaque risque non soldé génère une question, un destinataire, une pièce et une échéance « avant offre/promesse/acte » | INFO opérationnelle | Template déterministe | Envoyer la question au vendeur, syndic, notaire ou expert indiqué | Finding source et règle d’action |
