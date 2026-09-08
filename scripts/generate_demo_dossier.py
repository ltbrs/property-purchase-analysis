#!/usr/bin/env python3
"""Generate the lightweight, synthetic Lyon demo dossier.

The PDFs intentionally use only built-in Type 1 fonts and compressed text streams.
This keeps them small, searchable, and suitable for the same extraction pipeline as
user-uploaded PDFs. No third-party Python dependency is required.
"""

from __future__ import annotations

import hashlib
import json
import textwrap
import zlib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "demo-dossier-lyon"

DEMO_ADDRESS = "24 rue des Tisseurs, 69004 Lyon"
DEMO_NOTICE = "DOCUMENT SYNTHÉTIQUE DE DÉMONSTRATION • SANS VALEUR CONTRACTUELLE"

ElementKind = Literal[
    "h1", "lead", "h2", "body", "bullet", "kv", "callout", "small", "space"
]
# The unparameterized runtime alias keeps this dependency-free generator usable
# with the macOS system Python 3.8 as well as the project's Python 3.12.
Element = tuple


@dataclass(frozen=True)
class DemoDocument:
    logical_id: str
    filename: str
    title: str
    classification_hint: str
    issuer: str
    document_date: str | None
    covered_period_start: str | None
    covered_period_end: str | None
    purpose: str
    pages: list[list[Element]]


def E(kind: ElementKind, value: str = "") -> Element:
    return (kind, value)


DOCUMENTS = [
    DemoDocument(
        logical_id="fiche_synthetique",
        filename="01_fiche_synthetique_copropriete.pdf",
        title="Fiche synthétique de la copropriété",
        classification_hint="copro_financials",
        issuer="Régie Démo Lyon",
        document_date="2026-07-15",
        covered_period_start="2025-01-01",
        covered_period_end="2025-12-31",
        purpose="Identité, caractéristiques techniques et situation financière de la copropriété.",
        pages=[
            [
                E("h1", "Fiche synthétique de la copropriété"),
                E("lead", "Copropriété Les Tisseurs • mise à jour du 15/07/2026"),
                E("callout", "Adresse fictive : 24 rue des Tisseurs, 69004 Lyon"),
                E("h2", "Identification"),
                E("kv", "Nom d'usage|Copropriété Les Tisseurs"),
                E("kv", "Immatriculation|DEMO-RNC-69004-001 (identifiant fictif)"),
                E("kv", "Syndic|Régie Démo Lyon (entité fictive)"),
                E("kv", "Règlement initial|18 octobre 1987"),
                E("kv", "Bâtiment|Immeuble construit en 1898, élevé sur caves"),
                E("h2", "Organisation"),
                E("kv", "Lots inscrits|24 lots, dont 16 lots à usage d'habitation"),
                E("kv", "Syndic professionnel|Mandat du 30/06/2026 au 30/06/2027"),
                E("kv", "Gardien|Aucun"),
                E("kv", "Chauffage|Installations individuelles"),
            ],
            [
                E("h1", "Données financières essentielles"),
                E("lead", "Exercice clos le 31/12/2025"),
                E("kv", "Budget prévisionnel 2026|38 400 EUR"),
                E("kv", "Charges courantes 2025|36 920 EUR"),
                E("kv", "Impayés de la copropriété au 31/12/2025|21 600 EUR"),
                E("kv", "Dettes fournisseurs au 31/12/2025|4 150 EUR"),
                E("kv", "Fonds travaux au 31/12/2025|28 400 EUR"),
                E(
                    "kv",
                    "Quote-part fonds travaux attachée aux lots 18 et 42|1 420 EUR",
                ),
                E("h2", "Travaux"),
                E("bullet", "Réfection de toiture votée le 30/06/2026 : 96 000 EUR."),
                E("bullet", "Quote-part annoncée pour les lots 18 et 42 : 6 960 EUR."),
                E("bullet", "Trois appels de 2 320 EUR, du 15/10/2026 au 15/04/2027."),
                E(
                    "small",
                    "Données fabriquées exclusivement pour un scénario de démonstration.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="reglement_edd",
        filename="02_reglement_copropriete_et_edd.pdf",
        title="Règlement de copropriété et état descriptif de division",
        classification_hint="copro_rules",
        issuer="Étude notariale Démo Rhône",
        document_date="1987-10-18",
        covered_period_start=None,
        covered_period_end=None,
        purpose="Règles d'usage, définition des lots et répartition des charges.",
        pages=[
            [
                E("h1", "Règlement de copropriété"),
                E("lead", "Extrait synthétique pour le dossier de démonstration"),
                E(
                    "callout",
                    "Immeuble : 24 rue des Tisseurs, 69004 Lyon (adresse fictive)",
                ),
                E("h2", "Destination de l'immeuble"),
                E(
                    "body",
                    "L'immeuble est principalement destiné à l'habitation. Les activités professionnelles sans réception habituelle de clientèle sont admises sous réserve de ne causer aucune nuisance.",
                ),
                E("h2", "Parties communes"),
                E(
                    "bullet",
                    "Sol, gros œuvre, façades, toiture, réseaux collectifs et cage d'escalier.",
                ),
                E(
                    "bullet",
                    "La cour intérieure est une partie commune à jouissance collective.",
                ),
                E("h2", "Travaux privatifs"),
                E(
                    "body",
                    "Toute intervention affectant l'aspect extérieur, les murs porteurs ou les canalisations communes est soumise à autorisation préalable de l'assemblée générale.",
                ),
            ],
            [
                E("h1", "État descriptif de division"),
                E("lead", "Lots objets du projet de vente"),
                E("h2", "Lot n° 18"),
                E(
                    "body",
                    "Au troisième étage, porte gauche : appartement comprenant entrée, séjour, cuisine, deux chambres, salle d'eau et WC. Jouissance privative d'un grenier de rangement accessible depuis l'appartement.",
                ),
                E("kv", "Tantièmes généraux|700 / 10 000"),
                E("kv", "Tantièmes escalier|760 / 10 000"),
                E("kv", "Usage|Habitation"),
                E("h2", "Lot n° 42"),
                E("body", "Au sous-sol : une cave portant le numéro 7."),
                E("kv", "Tantièmes généraux|25 / 10 000"),
                E("h2", "Total vendu"),
                E("kv", "Tantièmes généraux|725 / 10 000"),
            ],
            [
                E("h1", "Répartition et règles particulières"),
                E("h2", "Charges générales"),
                E(
                    "body",
                    "Réparties selon les 10 000 tantièmes généraux. Les lots 18 et 42 représentent ensemble 725 / 10 000.",
                ),
                E("h2", "Charges d'escalier"),
                E(
                    "body",
                    "Réparties selon l'utilité objective de l'escalier. Le lot 18 supporte 760 / 10 000 de cette catégorie.",
                ),
                E("h2", "Restrictions"),
                E(
                    "bullet",
                    "La location touristique de courte durée à caractère commercial est interdite.",
                ),
                E(
                    "bullet",
                    "Aucun objet ne doit être entreposé dans les circulations communes.",
                ),
                E(
                    "bullet",
                    "Les revêtements de sol doivent préserver l'isolation acoustique existante.",
                ),
                E(
                    "small",
                    "Acte synthétique fictif. Il ne reproduit aucun règlement réel.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="ag_2024",
        filename="03_pv_assemblee_generale_2024.pdf",
        title="Procès-verbal d'assemblée générale 2024",
        classification_hint="ag_minutes",
        issuer="Régie Démo Lyon",
        document_date="2024-06-14",
        covered_period_start="2024-01-01",
        covered_period_end="2024-12-31",
        purpose="Première occurrence des infiltrations et décisions de gestion 2024.",
        pages=[
            [
                E("h1", "Procès-verbal de l'assemblée générale"),
                E("lead", "Réunion du 14/06/2024 • Copropriété Les Tisseurs"),
                E("kv", "Présents ou représentés|8 240 / 10 000 tantièmes"),
                E("kv", "Président de séance|Alex Martin (nom fictif)"),
                E("kv", "Secrétaire|Régie Démo Lyon"),
                E("h2", "Résolution 1 • Approbation des comptes"),
                E(
                    "body",
                    "Les comptes de l'exercice 2023, arrêtés à 34 610 EUR, sont approuvés. Résolution adoptée.",
                ),
                E("h2", "Résolution 2 • Budget prévisionnel"),
                E("body", "Le budget 2024 est fixé à 35 200 EUR. Résolution adoptée."),
            ],
            [
                E("h1", "Décisions techniques"),
                E("h2", "Résolution 7 • Infiltrations sous toiture"),
                E(
                    "callout",
                    "Des infiltrations ont été signalées sous le versant nord de la toiture après les pluies d'avril 2024.",
                ),
                E(
                    "body",
                    "L'assemblée décide de solliciter deux entreprises pour un diagnostic de couverture et des devis de réparation. Sujet discuté, aucun marché de travaux n'est voté à cette séance.",
                ),
                E("kv", "Statut|Discuté"),
                E("h2", "Résolution 8 • Réparation provisoire"),
                E(
                    "body",
                    "Une intervention conservatoire d'un montant maximal de 2 400 EUR est autorisée. Résolution adoptée.",
                ),
                E("small", "Fin du procès-verbal synthétique. Signatures fictives."),
            ],
        ],
    ),
    DemoDocument(
        logical_id="ag_2025",
        filename="04_pv_assemblee_generale_2025.pdf",
        title="Procès-verbal d'assemblée générale 2025",
        classification_hint="ag_minutes",
        issuer="Régie Démo Lyon",
        document_date="2025-06-20",
        covered_period_start="2025-01-01",
        covered_period_end="2025-12-31",
        purpose="Récurrence des infiltrations, impayés et préparation du projet toiture.",
        pages=[
            [
                E("h1", "Procès-verbal de l'assemblée générale"),
                E("lead", "Réunion du 20/06/2025 • Copropriété Les Tisseurs"),
                E("kv", "Présents ou représentés|7 980 / 10 000 tantièmes"),
                E("h2", "Résolution 1 • Approbation des comptes"),
                E(
                    "body",
                    "Les comptes 2024, arrêtés à 35 480 EUR, sont approuvés. Résolution adoptée.",
                ),
                E("h2", "Résolution 4 • Impayés"),
                E(
                    "callout",
                    "Le montant global des impayés de charges s'élève à 21 600 EUR au 31/05/2025.",
                ),
                E(
                    "body",
                    "L'assemblée autorise le syndic à poursuivre le recouvrement amiable puis judiciaire. Procédure en cours. Aucun impayé n'est affecté aux lots 18 et 42.",
                ),
            ],
            [
                E("h1", "Suivi de la toiture"),
                E("h2", "Résolution 9 • Nouvelles infiltrations"),
                E(
                    "callout",
                    "De nouvelles infiltrations sous le versant nord ont été constatées en février 2025 malgré la réparation provisoire.",
                ),
                E(
                    "body",
                    "L'assemblée prend connaissance du rapport de l'entreprise Couverture Démo. La réfection complète est estimée entre 88 000 EUR et 102 000 EUR.",
                ),
                E("kv", "Statut|Planifié"),
                E("h2", "Résolution 10 • Mission de maîtrise d'œuvre"),
                E(
                    "body",
                    "Une mission d'étude et de consultation est votée pour 4 800 EUR. Le choix des travaux est reporté à l'assemblée 2026.",
                ),
                E("small", "Fin du procès-verbal synthétique. Signatures fictives."),
            ],
        ],
    ),
    DemoDocument(
        logical_id="ag_2026",
        filename="05_pv_assemblee_generale_2026.pdf",
        title="Procès-verbal d'assemblée générale 2026",
        classification_hint="ag_minutes",
        issuer="Régie Démo Lyon",
        document_date="2026-06-30",
        covered_period_start="2026-01-01",
        covered_period_end="2026-12-31",
        purpose="Vote des travaux de toiture et calendrier des appels de fonds.",
        pages=[
            [
                E("h1", "Procès-verbal de l'assemblée générale"),
                E("lead", "Réunion du 30/06/2026 • Copropriété Les Tisseurs"),
                E("kv", "Présents ou représentés|8 610 / 10 000 tantièmes"),
                E("h2", "Résolution 1 • Approbation des comptes"),
                E(
                    "body",
                    "Les comptes 2025, arrêtés à 36 920 EUR, sont approuvés. Résolution adoptée.",
                ),
                E("h2", "Résolution 2 • Budget 2027"),
                E(
                    "body",
                    "Le budget prévisionnel 2027 est fixé à 40 800 EUR. Résolution adoptée.",
                ),
            ],
            [
                E("h1", "Travaux de toiture"),
                E("h2", "Résolution 8 • Réfection complète de la toiture"),
                E(
                    "callout",
                    "La réfection complète de la toiture est votée pour un montant total de 96 000 EUR TTC, honoraires inclus.",
                ),
                E(
                    "body",
                    "Le marché est attribué à Couverture Démo. Les travaux comprennent dépose, écran de sous-toiture, remplacement des éléments défectueux et reprise des évacuations d'eaux pluviales.",
                ),
                E("kv", "Statut|Voté"),
                E("kv", "Quote-part lots 18 et 42|6 960 EUR"),
                E("kv", "Début prévisionnel|Mars 2027"),
                E("h2", "Résolution 9 • Financement"),
                E(
                    "body",
                    "Trois appels égaux sont exigibles les 15/10/2026, 15/01/2027 et 15/04/2027. Résolution adoptée.",
                ),
            ],
            [
                E("h1", "Autres décisions"),
                E("h2", "Résolution 10 • Renforcement d'une poutre en cave"),
                E(
                    "callout",
                    "Le renforcement de la poutre sous la cour est voté pour 42 000 EUR TTC, avec une quote-part de 3 045 EUR pour les lots 18 et 42.",
                ),
                E(
                    "body",
                    "L'ingénieur a relevé une corrosion des appuis métalliques et recommande une intervention avant juin 2027. Statut : voté.",
                ),
                E("h2", "Résolution 12 • Ventilation des caves"),
                E(
                    "body",
                    "Une étude sur l'amélioration de la ventilation des caves est demandée après constat d'humidité. Budget d'étude maximal : 1 800 EUR. Statut : planifié.",
                ),
                E("h2", "Résolution 14 • Ravalement de façade"),
                E(
                    "body",
                    "Le projet de ravalement prévu au plan pluriannuel pour 2030 est présenté. Aucun travaux n'est voté à cette séance. Statut : discuté.",
                ),
                E("h2", "Résolution 16 • Renouvellement du syndic"),
                E(
                    "body",
                    "Le mandat de Régie Démo Lyon est renouvelé jusqu'au 30/06/2027.",
                ),
                E("small", "Fin du procès-verbal synthétique. Signatures fictives."),
            ],
        ],
    ),
    DemoDocument(
        logical_id="informations_financieres",
        filename="06_informations_financieres_copropriete.pdf",
        title="Informations financières préalables à la vente",
        classification_hint="copro_financials",
        issuer="Régie Démo Lyon",
        document_date="2026-08-28",
        covered_period_start="2024-01-01",
        covered_period_end="2026-08-28",
        purpose="Informations financières concernant la copropriété et les lots vendus.",
        pages=[
            [
                E("h1", "Informations financières préalables à la vente"),
                E("lead", "Lots 18 et 42 • situation au 28/08/2026"),
                E("kv", "Charges payées par le vendeur en 2024|1 780 EUR"),
                E("kv", "Charges payées par le vendeur en 2025|2 980 EUR"),
                E("kv", "Charges courantes appelées en 2026 au 28/08|2 040 EUR"),
                E("kv", "Arriéré du vendeur|0 EUR"),
                E("kv", "Avance de trésorerie attachée aux lots|310 EUR"),
                E("kv", "Fonds travaux attaché aux lots|1 420 EUR"),
                E("h2", "Situation globale de la copropriété"),
                E("kv", "Impayés au 31/12/2025|21 600 EUR"),
                E("kv", "Dettes fournisseurs au 31/12/2025|4 150 EUR"),
            ],
            [
                E("h1", "Sommes susceptibles d'être dues"),
                E("h2", "Travaux toiture votés le 30/06/2026"),
                E("kv", "Quote-part totale lots 18 et 42|6 960 EUR"),
                E("kv", "Appel n° 1, exigible le 15/10/2026|2 320 EUR"),
                E("kv", "Appel n° 2, exigible le 15/01/2027|2 320 EUR"),
                E("kv", "Appel n° 3, exigible le 15/04/2027|2 320 EUR"),
                E("h2", "Charges courantes"),
                E("kv", "Provision T4 2026, exigible le 01/10/2026|680 EUR"),
                E(
                    "callout",
                    "La répartition vendeur/acquéreur dépendra de l'acte et de la date de mutation. Ces montants ne préjugent pas de cette répartition.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="comptes_copro",
        filename="07_comptes_copropriete_2024_2025.pdf",
        title="Comptes de copropriété 2024 et 2025",
        classification_hint="copro_financials",
        issuer="Régie Démo Lyon",
        document_date="2026-06-30",
        covered_period_start="2024-01-01",
        covered_period_end="2025-12-31",
        purpose="Comparaison des comptes annuels et visibilité sur les impayés.",
        pages=[
            [
                E("h1", "Comptes approuvés • exercice 2024"),
                E("lead", "Période du 01/01/2024 au 31/12/2024"),
                E("kv", "Entretien et petites réparations|8 920 EUR"),
                E("kv", "Assurance immeuble|4 780 EUR"),
                E("kv", "Eau commune|6 410 EUR"),
                E("kv", "Honoraires et administration|7 260 EUR"),
                E("kv", "Autres charges|8 110 EUR"),
                E("kv", "Total charges copropriété|35 480 EUR"),
                E("kv", "Quote-part lots 18 et 42|1 780 EUR"),
            ],
            [
                E("h1", "Comptes approuvés • exercice 2025"),
                E("lead", "Période du 01/01/2025 au 31/12/2025"),
                E("kv", "Entretien et petites réparations|9 860 EUR"),
                E("kv", "Assurance immeuble|5 420 EUR"),
                E("kv", "Eau commune|6 880 EUR"),
                E("kv", "Honoraires et administration|7 540 EUR"),
                E("kv", "Autres charges|7 220 EUR"),
                E("kv", "Total charges copropriété|36 920 EUR"),
                E("kv", "Quote-part lots 18 et 42|2 980 EUR"),
                E("kv", "Impayés copropriété|21 600 EUR"),
                E(
                    "small",
                    "La hausse de la quote-part individuelle inclut régularisation d'eau et réparations provisoires de toiture.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="releve_charges",
        filename="08_releve_individuel_charges_2025_2026.pdf",
        title="Relevé individuel de charges",
        classification_hint="charges",
        issuer="Régie Démo Lyon",
        document_date="2026-08-28",
        covered_period_start="2025-01-01",
        covered_period_end="2026-12-31",
        purpose="Charges individuelles passées et provision courante à venir.",
        pages=[
            [
                E("h1", "Relevé individuel de charges"),
                E("lead", "Compte Camille Laurent • lots 18 et 42"),
                E("h2", "Exercice 2025"),
                E("kv", "Provisions appelées|2 440 EUR"),
                E("kv", "Régularisation eau|420 EUR"),
                E("kv", "Réparation provisoire toiture|120 EUR"),
                E("kv", "Total annuel du 01/01/2025 au 31/12/2025|2 980 EUR"),
                E("kv", "Solde au 31/12/2025|0 EUR"),
            ],
            [
                E("h1", "Appels courants 2026"),
                E("kv", "Provision T1, exigible le 01/01/2026|680 EUR"),
                E("kv", "Provision T2, exigible le 01/04/2026|680 EUR"),
                E("kv", "Provision T3, exigible le 01/07/2026|680 EUR"),
                E("kv", "Provision T4, exigible le 01/10/2026|680 EUR"),
                E("kv", "Total prévisionnel du 01/01/2026 au 31/12/2026|2 720 EUR"),
                E(
                    "callout",
                    "Les appels travaux toiture font l'objet d'un document distinct.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="appel_fonds_toiture",
        filename="09_appel_de_fonds_travaux_toiture.pdf",
        title="Appel de fonds travaux toiture",
        classification_hint="works_call",
        issuer="Régie Démo Lyon",
        document_date="2026-09-01",
        covered_period_start="2026-10-15",
        covered_period_end="2027-04-15",
        purpose="Échéancier nominatif correspondant aux travaux votés.",
        pages=[
            [
                E("h1", "Appel de fonds • travaux toiture"),
                E("lead", "Décision de l'AG du 30/06/2026, résolution 8"),
                E("kv", "Montant collectif voté|96 000 EUR TTC"),
                E("kv", "Lots concernés|18 et 42"),
                E("kv", "Quote-part individuelle totale|6 960 EUR"),
                E("h2", "Échéancier"),
                E("kv", "Appel n° 1, exigible le 15/10/2026|2 320 EUR"),
                E("kv", "Appel n° 2, exigible le 15/01/2027|2 320 EUR"),
                E("kv", "Appel n° 3, exigible le 15/04/2027|2 320 EUR"),
                E("callout", "Premier règlement à effectuer avant le 15/10/2026."),
            ],
        ],
    ),
    DemoDocument(
        logical_id="carnet_entretien",
        filename="10_carnet_entretien_immeuble.pdf",
        title="Carnet d'entretien de l'immeuble",
        classification_hint="maintenance_log",
        issuer="Régie Démo Lyon",
        document_date="2026-07-15",
        covered_period_start="2018-01-01",
        covered_period_end="2026-07-15",
        purpose="Historique d'entretien, contrats et travaux communs.",
        pages=[
            [
                E("h1", "Carnet d'entretien de l'immeuble"),
                E("lead", "Copropriété Les Tisseurs • mise à jour du 15/07/2026"),
                E("h2", "Caractéristiques"),
                E("kv", "Construction|1898"),
                E("kv", "Bâtiments|1 bâtiment sur caves, 4 étages"),
                E("kv", "Ascenseur|Aucun"),
                E("kv", "Chauffage collectif|Aucun"),
                E("kv", "Ventilation|Naturelle"),
                E("h2", "Contrats en cours"),
                E(
                    "bullet",
                    "Assurance multirisque immeuble, échéance annuelle au 31 décembre.",
                ),
                E("bullet", "Entretien des extincteurs, contrôle annuel en novembre."),
                E(
                    "bullet",
                    "Nettoyage des parties communes, contrat renouvelé le 01/07/2026.",
                ),
            ],
            [
                E("h1", "Historique des interventions"),
                E(
                    "kv",
                    "2018|Réfection partielle des réseaux d'eau en caves, 14 600 EUR",
                ),
                E("kv", "2021|Mise en peinture de la cage d'escalier, 18 900 EUR"),
                E(
                    "kv",
                    "2023|Contrôle et reprise de trois descentes d'eaux pluviales, 6 200 EUR",
                ),
                E(
                    "kv",
                    "2024|Réparation provisoire du versant nord de toiture, 2 280 EUR",
                ),
                E("kv", "2025|Étude de réfection complète de toiture, 4 800 EUR"),
                E("kv", "2026|Réfection complète votée, exécution prévue en mars 2027"),
                E("h2", "Observation"),
                E(
                    "body",
                    "Des traces d'humidité persistent dans deux caves. Une étude de ventilation a été décidée le 30/06/2026.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="dtg_pppt",
        filename="11_conclusions_dtg_et_pppt.pdf",
        title="Conclusions du DTG et projet de plan pluriannuel de travaux",
        classification_hint="maintenance_log",
        issuer="Bâti Conseil Démo",
        document_date="2026-03-12",
        covered_period_start="2026-01-01",
        covered_period_end="2035-12-31",
        purpose="État technique global et coûts futurs indicatifs sur dix ans.",
        pages=[
            [
                E("h1", "Diagnostic technique global"),
                E("lead", "Conclusions • visite du 12/03/2026"),
                E(
                    "callout",
                    "Rapport intégral fictif. Les conclusions servent uniquement au scénario de démonstration.",
                ),
                E("h2", "Clos et couvert"),
                E(
                    "bullet",
                    "Toiture : étanchéité dégradée sur le versant nord, intervention prioritaire.",
                ),
                E(
                    "bullet",
                    "Façades : enduits localement fissurés, sans désordre structurel visible.",
                ),
                E("h2", "Parties communes"),
                E("bullet", "Escalier : état d'usage satisfaisant."),
                E(
                    "bullet",
                    "Caves : humidité et renouvellement d'air insuffisant dans la zone nord.",
                ),
            ],
            [
                E("h1", "Synthèse des priorités"),
                E("h2", "Priorité 1 • 2026 à 2027"),
                E("kv", "Réfection complète de la toiture|96 000 EUR TTC"),
                E(
                    "body",
                    "Réduit le risque d'infiltration et protège la charpente. Travaux votés par l'AG du 30/06/2026.",
                ),
                E("h2", "Priorité 2 • 2027 à 2028"),
                E(
                    "kv",
                    "Ventilation et assainissement ponctuel des caves|18 000 EUR TTC",
                ),
                E("h2", "Priorité 3 • 2029 à 2031"),
                E(
                    "kv",
                    "Ravalement et traitement des fissures d'enduit|124 000 EUR TTC",
                ),
                E("h2", "Priorité 4 • 2032 à 2035"),
                E("kv", "Réfection de la cage d'escalier et éclairage|26 000 EUR TTC"),
            ],
            [
                E("h1", "Projet de plan pluriannuel de travaux"),
                E("lead", "Horizon 2026 à 2035"),
                E("kv", "Coût total indicatif|264 000 EUR TTC"),
                E("kv", "Travaux déjà votés|96 000 EUR TTC"),
                E("kv", "Travaux restant à décider|168 000 EUR TTC"),
                E("h2", "Limites"),
                E(
                    "body",
                    "Les montants constituent des estimations synthétiques. Seuls les travaux de toiture sont votés. Les autres opérations restent à étudier, chiffrer et soumettre aux assemblées futures.",
                ),
                E(
                    "body",
                    "Aucun désordre compromettant immédiatement la stabilité générale de l'immeuble n'a été constaté lors de la visite visuelle.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="dpe",
        filename="12_diagnostic_performance_energetique.pdf",
        title="Diagnostic de performance énergétique",
        classification_hint="dpe",
        issuer="Diagnostics Démo Rhône",
        document_date="2026-08-25",
        covered_period_start=None,
        covered_period_end=None,
        purpose="Performance énergétique, émissions, coûts et recommandations.",
        pages=[
            [
                E("h1", "Diagnostic de performance énergétique"),
                E("lead", "Logement existant • établi le 25/08/2026"),
                E(
                    "callout",
                    "Identifiant : DEMO-DPE-LYON-001 • non interrogeable dans le registre ADEME",
                ),
                E("kv", "Adresse|24 rue des Tisseurs, 69004 Lyon"),
                E("kv", "Lot principal|18"),
                E("kv", "Surface habitable prise en compte|64,80 m²"),
                E("kv", "Année de construction|1898"),
                E("kv", "Type|Appartement au 3e étage"),
                E("kv", "Date de visite|25/08/2026"),
                E("kv", "Valable jusqu'au|24/08/2036"),
            ],
            [
                E("h1", "Performance énergétique"),
                E("lead", "Méthode conventionnelle 3CL"),
                E("callout", "Classe énergie : E"),
                E("kv", "Consommation énergie primaire|302 kWh/m²/an"),
                E("kv", "Émissions de gaz à effet de serre|9 kg CO2/m²/an"),
                E("kv", "Classe climat|B"),
                E("kv", "Chauffage|Électrique individuel, radiateurs à effet Joule"),
                E("kv", "Eau chaude sanitaire|Ballon électrique individuel"),
                E(
                    "kv",
                    "Estimation des coûts annuels|Entre 1 880 EUR et 2 650 EUR par an",
                ),
                E(
                    "small",
                    "Prix moyens des énergies indexés sur les années de référence du diagnostic fictif.",
                ),
            ],
            [
                E("h1", "Recommandations"),
                E("h2", "Travaux prioritaires"),
                E(
                    "bullet",
                    "Isoler les rampants donnant sur le grenier privatif, sous réserve des autorisations nécessaires.",
                ),
                E(
                    "bullet",
                    "Remplacer les radiateurs les plus anciens par des appareils à régulation électronique.",
                ),
                E(
                    "bullet",
                    "Améliorer l'étanchéité à l'air des menuiseries sans dégrader la ventilation.",
                ),
                E("h2", "Scénario indicatif"),
                E(
                    "body",
                    "Après isolation ciblée et régulation du chauffage, le gain estimé pourrait être de 45 à 60 kWh/m²/an. Cette estimation ne constitue ni un devis ni un audit énergétique.",
                ),
                E(
                    "small",
                    "Diagnostiqueur, certification et assurance : références fictives réservées à la démonstration.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="diagnostics",
        filename="13_dossier_diagnostics_techniques.pdf",
        title="Dossier de diagnostics techniques",
        classification_hint="diagnostics",
        issuer="Diagnostics Démo Rhône",
        document_date="2026-08-25",
        covered_period_start=None,
        covered_period_end=None,
        purpose="Carrez, amiante, plomb, électricité et gaz dans un PDF page-citable.",
        pages=[
            [
                E("h1", "Attestation de superficie privative"),
                E("lead", "Mesurage loi Carrez • visite du 25/08/2026"),
                E("kv", "Lot mesuré|Lot principal n° 18"),
                E("callout", "Superficie privative mesurée : 61,50 m²"),
                E("kv", "Surface au sol totale|66,10 m²"),
                E(
                    "body",
                    "Les surfaces sous hauteur inférieure à 1,80 m et les embrasures ont été exclues du mesurage privatif.",
                ),
                E("small", "Mesurage fictif. Aucun relevé physique n'a été réalisé."),
            ],
            [
                E("h1", "État mentionnant la présence d'amiante"),
                E("lead", "Repérage du 25/08/2026"),
                E(
                    "callout",
                    "Présence d'amiante repérée dans un conduit en fibrociment situé dans le placard de l'entrée.",
                ),
                E("kv", "État de conservation|Non dégradé lors de la visite"),
                E("kv", "Préconisation|Évaluation périodique et absence de percement"),
                E(
                    "body",
                    "Aucun autre matériau ou produit contenant de l'amiante n'a été identifié dans le périmètre de la mission.",
                ),
                E(
                    "small",
                    "Résultat synthétique fictif, sans portée sanitaire ou technique.",
                ),
            ],
            [
                E("h1", "Constat de risque d'exposition au plomb"),
                E("lead", "CREP réalisé le 25/08/2026"),
                E(
                    "callout",
                    "Présence de plomb au-dessus du seuil sur deux unités de diagnostic des fenêtres du séjour.",
                ),
                E(
                    "kv",
                    "Résultat|Deux unités de classe 2, revêtements en état d'usage",
                ),
                E("kv", "Facteurs de dégradation du bâti|Aucun relevé"),
                E(
                    "body",
                    "Quelques unités de diagnostic n'ont pas pu être mesurées derrière des meubles fixes et sont signalées comme non accessibles.",
                ),
            ],
            [
                E("h1", "État de l'installation intérieure d'électricité"),
                E("lead", "Installation de plus de 15 ans • contrôle du 25/08/2026"),
                E(
                    "callout",
                    "Anomalie : absence de protection différentielle 30 mA adaptée sur deux circuits alimentant la salle d'eau.",
                ),
                E("bullet", "Anomalie B3.3.6 : protection différentielle à compléter."),
                E(
                    "bullet",
                    "Anomalie B7.3 : matériel ancien présentant un risque de contact direct dans le tableau secondaire.",
                ),
                E("kv", "Mesure recommandée|Intervention d'un électricien qualifié"),
                E(
                    "body",
                    "Le diagnostic constate des anomalies. Il ne constitue pas une attestation de conformité.",
                ),
            ],
            [
                E("h1", "État de l'installation intérieure de gaz"),
                E("lead", "Constat du 25/08/2026"),
                E(
                    "callout",
                    "Aucune installation intérieure fixe de gaz n'est présente dans le logement.",
                ),
                E("kv", "Résultat|Sans objet"),
                E("kv", "Chauffage|Électrique individuel"),
                E("kv", "Production d'eau chaude|Ballon électrique"),
                E(
                    "body",
                    "Aucune bouteille de gaz ni canalisation fixe alimentant un appareil n'a été constatée dans le périmètre visité.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="erp_termites_bruit",
        filename="14_etat_risques_termites_et_bruit.pdf",
        title="État des risques, termites et bruit",
        classification_hint="risk_statement",
        issuer="Diagnostics Démo Rhône",
        document_date="2026-08-25",
        covered_period_start=None,
        covered_period_end=None,
        purpose="Informations environnementales et états locaux applicables au scénario lyonnais.",
        pages=[
            [
                E("h1", "État des risques et pollutions"),
                E("lead", "Établi le 25/08/2026 • valable jusqu'au 24/02/2027"),
                E(
                    "callout",
                    "Scénario fictif : exposition faible au retrait-gonflement des argiles identifiée pour la parcelle de démonstration.",
                ),
                E(
                    "kv",
                    "Plan de prévention des risques naturels|Information présente, aucune prescription de travaux indiquée",
                ),
                E("kv", "Sismicité|Zone 2, faible"),
                E("kv", "Radon|Potentiel de catégorie 1 dans ce scénario"),
                E(
                    "kv",
                    "Secteur d'information sur les sols|Non identifié dans ce scénario",
                ),
                E(
                    "body",
                    "Ce relevé est fabriqué pour la démonstration et ne doit jamais servir à apprécier un emplacement réel.",
                ),
            ],
            [
                E("h1", "État relatif à la présence de termites"),
                E(
                    "lead",
                    "Inspection visuelle du 25/08/2026 • valable jusqu'au 24/02/2027",
                ),
                E(
                    "callout",
                    "Absence d'indice d'infestation de termites dans les parties privatives visitées.",
                ),
                E(
                    "kv",
                    "Zone préfectorale|Bien présenté comme situé dans un périmètre concerné",
                ),
                E(
                    "kv",
                    "Boiseries examinées|Plinthes, huisseries et plancher accessibles",
                ),
                E("kv", "Limites|Cave encombrée, contrôle visuel partiel"),
                E(
                    "body",
                    "L'absence d'indice le jour de la visite ne garantit pas l'absence future d'infestation.",
                ),
            ],
            [
                E("h1", "État des nuisances sonores aériennes"),
                E("lead", "Situation déclarée au 25/08/2026"),
                E(
                    "callout",
                    "Le bien de démonstration est présenté comme situé hors zone d'un plan d'exposition au bruit d'aérodrome.",
                ),
                E("kv", "Plan d'exposition au bruit|Non concerné dans ce scénario"),
                E(
                    "body",
                    "Cet état ne mesure pas les bruits de voisinage, de circulation routière, ferroviaire ou liés aux activités urbaines.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="taxe_fonciere",
        filename="15_avis_taxe_fonciere_2026.pdf",
        title="Avis de taxe foncière 2026",
        classification_hint="property_tax",
        issuer="Administration fiscale fictive",
        document_date="2026-08-20",
        covered_period_start="2026-01-01",
        covered_period_end="2026-12-31",
        purpose="Repère annuel de fiscalité locale pour le budget acquéreur.",
        pages=[
            [
                E("h1", "Avis de taxe foncière 2026"),
                E("lead", "Simulation sans lien avec l'administration fiscale"),
                E("kv", "Propriétaire fictif|Camille Laurent"),
                E("kv", "Bien|24 rue des Tisseurs, 69004 Lyon • lots 18 et 42"),
                E("kv", "Taxe foncière bâtie|1 084 EUR"),
                E("kv", "Taxe d'enlèvement des ordures ménagères|196 EUR"),
                E("callout", "Montant total simulé : 1 280 EUR"),
                E("kv", "Date limite simulée|15/10/2026"),
                E(
                    "small",
                    "Ce document n'est pas un avis fiscal et ne reprend aucun identifiant fiscal réel.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="cil",
        filename="16_carnet_information_logement.pdf",
        title="Carnet d'information du logement",
        classification_hint="maintenance_log",
        issuer="Propriétaire fictif",
        document_date="2026-08-28",
        covered_period_start="2019-01-01",
        covered_period_end="2026-08-28",
        purpose="Travaux et équipements connus à l'échelle du logement.",
        pages=[
            [
                E("h1", "Carnet d'information du logement"),
                E("lead", "Lot 18 • mise à jour du 28/08/2026"),
                E("kv", "Adresse|24 rue des Tisseurs, 69004 Lyon"),
                E("kv", "Surface habitable déclarée|64,80 m²"),
                E("kv", "Chauffage|Radiateurs électriques individuels"),
                E("kv", "Eau chaude|Ballon électrique 150 litres"),
                E("kv", "Ventilation|Ventilation naturelle par conduits"),
                E("h2", "Documents associés"),
                E("bullet", "DPE établi le 25/08/2026."),
                E("bullet", "Diagnostics techniques établis le 25/08/2026."),
            ],
            [
                E("h1", "Travaux connus dans le logement"),
                E("kv", "2019|Remplacement des fenêtres sur rue par double vitrage"),
                E("kv", "2020|Installation du ballon d'eau chaude électrique"),
                E(
                    "kv",
                    "2022|Rénovation de la cuisine sans modification de mur porteur",
                ),
                E("kv", "2024|Remplacement de deux radiateurs électriques"),
                E("h2", "Documents non disponibles"),
                E(
                    "body",
                    "Aucune facture d'isolation des rampants n'est disponible. Le DPE recommande d'étudier cette intervention.",
                ),
                E(
                    "small",
                    "Carnet fictif limité aux informations déclarées pour la démonstration.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="titre_propriete",
        filename="17_attestation_titre_propriete.pdf",
        title="Attestation synthétique de propriété",
        classification_hint="unknown",
        issuer="Étude notariale Démo Rhône",
        document_date="2018-11-09",
        covered_period_start=None,
        covered_period_end=None,
        purpose="Contexte de propriété, désignation et servitudes connues.",
        pages=[
            [
                E("h1", "Attestation synthétique de propriété"),
                E("lead", "Copie fictive destinée à la démonstration"),
                E("kv", "Propriétaire|Camille Laurent (identité fictive)"),
                E("kv", "Date d'acquisition|09/11/2018"),
                E("kv", "Adresse|24 rue des Tisseurs, 69004 Lyon"),
                E("kv", "Lots|Lot 18, appartement • lot 42, cave"),
                E("kv", "Origine de propriété|Acquisition par acte reçu le 09/11/2018"),
                E("h2", "Désignation"),
                E(
                    "body",
                    "Appartement au troisième étage, porte gauche, et cave n° 7 au sous-sol, conformément à l'état descriptif de division fictif.",
                ),
            ],
            [
                E("h1", "Charges et servitudes mentionnées"),
                E(
                    "bullet",
                    "Servitude de passage des réseaux communs dans les gaines techniques.",
                ),
                E(
                    "bullet",
                    "Droit d'accès de la copropriété aux conduites communes après information de l'occupant.",
                ),
                E(
                    "bullet",
                    "Aucune hypothèque ni inscription réelle n'est reproduite dans cette démonstration.",
                ),
                E(
                    "callout",
                    "Cette attestation n'émane d'aucun notaire et ne prouve aucun droit de propriété.",
                ),
            ],
        ],
    ),
    DemoDocument(
        logical_id="notice_copro",
        filename="18_notice_information_copropriete.pdf",
        title="Notice d'information relative à la copropriété",
        classification_hint="unknown",
        issuer="Régie Démo Lyon",
        document_date="2026-08-28",
        covered_period_start=None,
        covered_period_end=None,
        purpose="Notice d'information sur le fonctionnement et les obligations de la copropriété.",
        pages=[
            [
                E("h1", "Notice d'information relative à la copropriété"),
                E("lead", "Résumé pédagogique joint au dossier de démonstration"),
                E("h2", "Organisation"),
                E(
                    "bullet",
                    "Le syndicat des copropriétaires prend les décisions collectives en assemblée générale.",
                ),
                E(
                    "bullet",
                    "Le syndic exécute les décisions et administre l'immeuble dans le cadre de son mandat.",
                ),
                E("bullet", "Le conseil syndical assiste et contrôle le syndic."),
                E("h2", "Participation aux décisions"),
                E(
                    "body",
                    "Chaque copropriétaire est convoqué, peut participer, voter ou se faire représenter. Les majorités varient selon la nature de la décision.",
                ),
            ],
            [
                E("h1", "Droits et obligations"),
                E(
                    "bullet",
                    "Respecter la destination de l'immeuble et le règlement de copropriété.",
                ),
                E(
                    "bullet",
                    "Payer les provisions et appels de fonds aux dates d'exigibilité.",
                ),
                E(
                    "bullet",
                    "Informer le syndic des travaux privatifs affectant des parties communes.",
                ),
                E(
                    "bullet",
                    "Contribuer au fonds travaux selon les règles applicables à la copropriété.",
                ),
                E("h2", "Mutation"),
                E(
                    "body",
                    "Les informations financières et techniques du lot et de la copropriété doivent être examinées avant l'engagement. Le notaire organise les formalités propres à la vente.",
                ),
                E(
                    "small",
                    "Cette notice simplifiée ne remplace pas la notice réglementaire ni un conseil professionnel.",
                ),
            ],
        ],
    ),
]


PREFIX_PAGES: dict[str, list[list[Element]]] = {
    "diagnostics": [
        [
            E("h1", "Dossier de diagnostics techniques"),
            E("lead", "Rapport n° DDT-DEMO-2026-0825 • édition du 28/08/2026"),
            E(
                "callout",
                "Document entièrement fictif, établi sans visite et sans diagnostiqueur réel.",
            ),
            E("kv", "Nature du bien|Appartement en copropriété"),
            E("kv", "Adresse|24 rue des Tisseurs, 69004 Lyon"),
            E("kv", "Étage et porte|3e étage, porte gauche"),
            E("kv", "Lots examinés|Lot 18 et accès visuel à la cave du lot 42"),
            E("kv", "Propriétaire déclaré|Camille Laurent, identité fictive"),
            E("kv", "Date de visite simulée|25/08/2026"),
            E("kv", "Opérateur|Morgan Vidal, identité fictive"),
            E(
                "small",
                "Le document est volontairement construit comme un rapport de diagnostic courant, sans photo ni signature exploitable.",
            ),
        ],
        [
            E("h1", "Note de synthèse des conclusions"),
            E(
                "lead",
                "Lecture rapide, se reporter à chaque rapport pour le périmètre et les limites",
            ),
            E("kv", "Superficie privative|61,50 m²"),
            E(
                "kv",
                "Amiante|Présence dans un conduit en fibrociment, état non dégradé",
            ),
            E("kv", "Plomb|Deux unités de classe 2 sur les fenêtres du séjour"),
            E("kv", "Électricité|Anomalies B3.3.6 et B7.3"),
            E("kv", "Gaz|Installation fixe absente, diagnostic sans objet"),
            E("kv", "Termites|Aucun indice dans les zones accessibles"),
            E("kv", "DPE|Document distinct, classe E"),
            E(
                "callout",
                "Points nécessitant une lecture attentive : électricité, plomb, amiante et cave partiellement accessible.",
            ),
        ],
    ]
}


EXTRA_PAGES: dict[str, list[list[Element]]] = {
    "fiche_synthetique": [
        [
            E("h1", "Caractéristiques techniques complémentaires"),
            E("kv", "Parcelle de démonstration|Section DEMO, numéro 0042"),
            E("kv", "Surface au sol de l'immeuble|410 m², valeur déclarative fictive"),
            E("kv", "Nombre de bâtiments|1"),
            E("kv", "Nombre d'escaliers|1"),
            E("kv", "Ascenseur|Non"),
            E("kv", "Type de couverture|Tuiles mécaniques sur charpente bois"),
            E("kv", "Réseau d'eau|Branchement collectif avec sous-comptage"),
            E("kv", "Production d'eau chaude|Individuelle"),
            E("kv", "Étiquette DPE collectif|Non renseignée"),
            E(
                "small",
                "Les valeurs techniques non utiles à l'analyse du lot sont conservées pour reproduire la densité d'une fiche réelle.",
            ),
        ],
        [
            E("h1", "Indicateurs comptables détaillés"),
            E("kv", "Créances exigibles au 31/12/2025|24 910 EUR"),
            E("kv", "Dont impayés supérieurs à 90 jours|21 600 EUR"),
            E("kv", "Trésorerie disponible|19 740 EUR"),
            E("kv", "Compte séparé fonds travaux|28 400 EUR"),
            E("kv", "Nombre de copropriétaires débiteurs|3 sur 16"),
            E("kv", "Procédure collective|Aucune"),
            E("kv", "Mandataire ad hoc|Non"),
            E("kv", "Administrateur provisoire|Non"),
            E("h2", "Événements postérieurs"),
            E(
                "body",
                "Les travaux de toiture et le renforcement de la poutre en cave ont été votés le 30/06/2026. Ils ne figurent pas dans les comptes clos au 31/12/2025.",
            ),
        ],
    ],
    "reglement_edd": [
        [
            E("h1", "Définitions et jouissance des locaux"),
            E("h2", "Parties privatives"),
            E(
                "body",
                "Les cloisons non porteuses, revêtements, équipements intérieurs et canalisations à usage exclusif sont privatifs dans les limites du règlement.",
            ),
            E("h2", "Parties communes spéciales"),
            E(
                "bullet",
                "L'escalier, ses paliers et son éclairage sont communs aux lots desservis.",
            ),
            E("bullet", "La toiture et la charpente sont communes à tous les lots."),
            E(
                "bullet",
                "Les caves sont privatives, leurs murs porteurs et réseaux restent communs.",
            ),
            E("h2", "Accès"),
            E(
                "body",
                "L'accès principal s'effectue par le hall sur rue. L'accès aux caves s'effectue par l'escalier intérieur. Ces indications sont purement descriptives.",
            ),
        ],
        [
            E("h1", "Règles de vie courante"),
            E(
                "bullet",
                "Les travaux bruyants sont annoncés au syndic et limités aux horaires admis par les règles locales.",
            ),
            E(
                "bullet",
                "Les vélos ne sont pas stationnés dans le hall ni sur les paliers.",
            ),
            E(
                "bullet",
                "Les fenêtres et volets visibles depuis la rue conservent un aspect harmonisé.",
            ),
            E(
                "bullet",
                "Les animaux sont admis sous réserve de l'absence de nuisance.",
            ),
            E("bullet", "Le séchage du linge aux fenêtres sur rue est interdit."),
            E("h2", "Assurances"),
            E(
                "body",
                "Chaque occupant assure ses risques privatifs. Le syndicat souscrit les assurances relatives aux parties communes.",
            ),
            E(
                "small",
                "Ces clauses de remplissage donnent au document une longueur comparable à un extrait de règlement sans créer de nouvelle conclusion de risque.",
            ),
        ],
        [
            E("h1", "Historique des actes modificatifs"),
            E(
                "kv",
                "18/10/1987|Établissement du règlement et de l'état descriptif de division",
            ),
            E(
                "kv",
                "12/04/1996|Réunion de deux anciennes chambres de service au lot 18",
            ),
            E("kv", "07/09/2008|Mise à jour de la répartition des charges d'escalier"),
            E(
                "kv",
                "16/02/2017|Adaptation des clauses relatives à l'usage professionnel",
            ),
            E("kv", "04/11/2022|Interdiction de la location touristique commerciale"),
            E("h2", "Publication"),
            E(
                "body",
                "Toutes les références de formalité et de volume sont fictives et volontairement non conformes à un identifiant de publicité foncière.",
            ),
        ],
    ],
    "ag_2024": [
        [
            E("h1", "Résolutions courantes et contrats"),
            E("kv", "Résolution 3|Contrat d'assurance renouvelé, adopté"),
            E(
                "kv",
                "Résolution 4|Nettoyage des communs renouvelé pour 3 480 EUR/an, adopté",
            ),
            E("kv", "Résolution 5|Contrôle des extincteurs, adopté"),
            E(
                "kv",
                "Résolution 6|Mise à jour des coordonnées des occupants, information",
            ),
            E("h2", "Résolution 9 • Façade cour"),
            E(
                "body",
                "Des fissures d'enduit et des traces d'humidité sont signalées sur la façade cour. Le conseil syndical est chargé de recueillir un avis technique. Sujet discuté.",
            ),
            E("h2", "Questions diverses"),
            E(
                "body",
                "Rappel concernant les poussettes dans le hall, remplacement de deux ampoules et demande de réglage du ferme-porte.",
            ),
        ],
        [
            E("h1", "Feuille de présence synthétique"),
            E("kv", "Copropriétaires présents|9"),
            E("kv", "Pouvoirs reçus|4"),
            E("kv", "Absents non représentés|3"),
            E("kv", "Tantièmes représentés|8 240 / 10 000"),
            E("kv", "Ouverture de séance|18 h 12"),
            E("kv", "Clôture de séance|20 h 06"),
            E("h2", "Pièces annexées"),
            E("bullet", "État des dépenses 2023."),
            E("bullet", "Projet de budget 2024."),
            E("bullet", "Compte rendu de l'intervention provisoire en toiture."),
        ],
    ],
    "ag_2025": [
        [
            E("h1", "Façade et contentieux"),
            E("h2", "Résolution 11 • Façade cour"),
            E(
                "body",
                "Les fissures d'enduit déjà signalées en 2024 restent visibles. Une campagne de sondages est proposée avec le futur ravalement. Sujet discuté, sans vote de travaux.",
            ),
            E("h2", "Résolution 12 • Litige avec l'entreprise d'étanchéité"),
            E(
                "callout",
                "Une procédure amiable est en cours contre l'entreprise ayant réalisé la réparation provisoire de toiture. Réclamation déclarée : 18 500 EUR.",
            ),
            E(
                "body",
                "L'assureur demande une expertise contradictoire. Aucun accord ni indemnisation n'est obtenu à la date de l'assemblée. Statut : en cours.",
            ),
            E("h2", "Résolution 13 • Conseil juridique"),
            E(
                "body",
                "Une enveloppe maximale de 3 000 EUR est autorisée pour les frais d'expertise et de conseil.",
            ),
        ],
        [
            E("h1", "Budget, présence et annexes"),
            E("kv", "Budget prévisionnel 2025|37 600 EUR"),
            E("kv", "Budget prévisionnel 2026|38 400 EUR"),
            E("kv", "Tantièmes représentés|7 980 / 10 000"),
            E("kv", "Ouverture de séance|18 h 18"),
            E("kv", "Clôture de séance|21 h 04"),
            E("h2", "Informations sans vote"),
            E(
                "bullet",
                "Le relevé des compteurs d'eau aura lieu au mois de septembre.",
            ),
            E(
                "bullet",
                "Le conseil syndical recherche un nouveau prestataire pour les boîtes aux lettres.",
            ),
            E(
                "bullet",
                "Les encombrants déposés dans la cour doivent être retirés par leurs propriétaires.",
            ),
        ],
    ],
    "ag_2026": [
        [
            E("h1", "Comparaison des offres de travaux"),
            E("lead", "Annexe aux résolutions 8 et 10"),
            E("kv", "Toiture, offre A|91 400 EUR TTC, hors honoraires"),
            E("kv", "Toiture, offre B|88 600 EUR TTC, hors honoraires"),
            E("kv", "Marché retenu avec honoraires|96 000 EUR TTC"),
            E("kv", "Poutre, offre A|42 000 EUR TTC, retenue"),
            E("kv", "Poutre, offre B|47 800 EUR TTC"),
            E("h2", "Réserves"),
            E(
                "body",
                "Les quantités pourront évoluer après ouverture des ouvrages. Toute modification dépassant 5 % doit être soumise au conseil syndical puis ratifiée selon les règles applicables.",
            ),
        ],
        [
            E("h1", "Présence, scrutins et calendrier"),
            E("kv", "Tantièmes représentés|8 610 / 10 000"),
            E("kv", "Vote toiture, pour|7 940 / 8 610"),
            E("kv", "Vote poutre, pour|8 120 / 8 610"),
            E("kv", "Ouverture de séance|18 h 05"),
            E("kv", "Clôture de séance|21 h 42"),
            E("kv", "Notification du procès-verbal|12/07/2026"),
            E("h2", "Calendrier indicatif"),
            E(
                "body",
                "Installation de chantier prévue en mars 2027, sous réserve des autorisations, de la météo et du versement des appels de fonds.",
            ),
        ],
    ],
    "informations_financieres": [
        [
            E("h1", "Travaux structurels votés"),
            E("lead", "Résolution 10 de l'AG du 30/06/2026"),
            E("kv", "Montant collectif|42 000 EUR TTC"),
            E("kv", "Quote-part lots 18 et 42|3 045 EUR"),
            E("kv", "Appel n° 1, exigible le 15/11/2026|1 522,50 EUR"),
            E("kv", "Appel n° 2, exigible le 15/03/2027|1 522,50 EUR"),
            E(
                "callout",
                "Exposition totale explicite aux deux travaux votés : 10 005 EUR pour les lots 18 et 42.",
            ),
            E(
                "body",
                "Ce total additionne 6 960 EUR de toiture et 3 045 EUR de renforcement de poutre. Il exclut les charges courantes.",
            ),
        ],
        [
            E("h1", "Situation du compte vendeur"),
            E("kv", "Solde au 28/08/2026|Créditeur de 42 EUR"),
            E("kv", "Dernier règlement|680 EUR reçu le 03/07/2026"),
            E("kv", "Contentieux personnel|Aucun"),
            E("kv", "Prêt collectif souscrit|Aucun"),
            E("kv", "Emprunt du syndicat en cours|Aucun"),
            E("h2", "Coordonnées comptables"),
            E(
                "body",
                "Référence interne du compte : LOT18-42-DEMO. IBAN, références bancaires et coordonnées individuelles sont volontairement omis.",
            ),
            E(
                "small",
                "Les chiffres sont une photographie fictive et peuvent se répéter dans d'autres pièces afin de permettre les rapprochements automatiques.",
            ),
        ],
    ],
    "comptes_copro": [
        [
            E("h1", "Balance simplifiée au 31/12/2025"),
            E("kv", "Banque compte courant|19 740 EUR"),
            E("kv", "Compte séparé fonds travaux|28 400 EUR"),
            E("kv", "Créances copropriétaires|24 910 EUR"),
            E("kv", "Dettes fournisseurs|4 150 EUR"),
            E("kv", "Produits à recevoir|1 380 EUR"),
            E("kv", "Charges constatées d'avance|760 EUR"),
            E("h2", "Alerte de gestion"),
            E(
                "body",
                "Trois comptes représentent l'essentiel des 21 600 EUR d'impayés supérieurs à 90 jours. Des démarches de recouvrement sont en cours.",
            ),
        ],
        [
            E("h1", "Répartition indicative du lot"),
            E("kv", "Charges générales 2025|1 970 EUR"),
            E("kv", "Charges escalier 2025|420 EUR"),
            E("kv", "Eau et relevé individuel 2025|470 EUR"),
            E("kv", "Réparation provisoire toiture|120 EUR"),
            E("kv", "Total lots 18 et 42|2 980 EUR"),
            E("h2", "Écart par rapport à 2024"),
            E(
                "callout",
                "La quote-part passe de 1 780 EUR en 2024 à 2 980 EUR en 2025, soit une hausse de 1 200 EUR.",
            ),
            E(
                "body",
                "L'évolution provient principalement de la régularisation d'eau, de l'assurance et des interventions liées à la toiture.",
            ),
        ],
    ],
    "releve_charges": [
        [
            E("h1", "Détail des opérations 2025"),
            E("kv", "01/01/2025|Provision trimestrielle : 610 EUR"),
            E("kv", "01/04/2025|Provision trimestrielle : 610 EUR"),
            E("kv", "01/07/2025|Provision trimestrielle : 610 EUR"),
            E("kv", "01/10/2025|Provision trimestrielle : 610 EUR"),
            E("kv", "15/12/2025|Régularisation eau : 420 EUR"),
            E("kv", "15/12/2025|Réparation toiture : 120 EUR"),
            E("kv", "Total|2 980 EUR"),
        ],
        [
            E("h1", "Informations de répartition"),
            E("kv", "Clé générale|725 / 10 000"),
            E("kv", "Clé escalier|760 / 10 000"),
            E("kv", "Index eau au 31/12/2025|418,6 m³, valeur fictive"),
            E("kv", "Index eau au 31/12/2024|389,1 m³, valeur fictive"),
            E("kv", "Consommation enregistrée|29,5 m³"),
            E("h2", "Observation"),
            E(
                "body",
                "Le relevé contient des informations de comptage utiles au calcul des charges mais sans incidence directe sur les principaux constats du rapport.",
            ),
        ],
    ],
    "appel_fonds_toiture": [
        [
            E("h1", "Appel de fonds • renforcement structurel"),
            E("lead", "Décision de l'AG du 30/06/2026, résolution 10"),
            E("kv", "Objet|Renforcement de la poutre sous la cour"),
            E("kv", "Montant collectif voté|42 000 EUR TTC"),
            E("kv", "Quote-part lots 18 et 42|3 045 EUR"),
            E("kv", "Appel n° 1, exigible le 15/11/2026|1 522,50 EUR"),
            E("kv", "Appel n° 2, exigible le 15/03/2027|1 522,50 EUR"),
            E("callout", "Ce projet est distinct de la réfection de toiture."),
        ],
        [
            E("h1", "Modalités pratiques"),
            E("bullet", "Rappeler la référence LOT18-42-DEMO lors du règlement."),
            E(
                "bullet",
                "Les coordonnées bancaires ne sont pas reproduites dans le document synthétique.",
            ),
            E(
                "bullet",
                "Toute contestation comptable est adressée au syndic fictif avec copie du relevé.",
            ),
            E("h2", "Récapitulatif des travaux"),
            E("kv", "Toiture|6 960 EUR pour les lots vendus"),
            E("kv", "Poutre|3 045 EUR pour les lots vendus"),
            E("kv", "Total|10 005 EUR"),
            E(
                "small",
                "La répartition entre vendeur et acquéreur n'est pas déterminée par cet appel synthétique.",
            ),
        ],
    ],
    "carnet_entretien": [
        [
            E("h1", "Contrôles périodiques"),
            E(
                "kv",
                "Extincteurs|Contrôle du 18/11/2025, prochaine visite novembre 2026",
            ),
            E("kv", "Éclairage de sécurité|Essai du 18/11/2025"),
            E("kv", "Porte d'entrée|Réglage du ferme-porte le 04/02/2026"),
            E("kv", "Colonnes d'eau|Recherche de fuite le 22/03/2026"),
            E("kv", "Nettoyage des chéneaux|Intervention du 16/10/2025"),
            E("h2", "Petites interventions"),
            E(
                "body",
                "Remplacement d'ampoules, réglages de minuterie, reprise d'une poignée et débouchage ponctuel d'une évacuation en cour.",
            ),
        ],
        [
            E("h1", "Sinistres et observations"),
            E("kv", "Avril 2024|Infiltration sous toiture, versant nord"),
            E("kv", "Février 2025|Nouvelle infiltration, même zone"),
            E("kv", "Décembre 2025|Humidité relevée dans les caves nord"),
            E(
                "kv",
                "Mai 2026|Corrosion observée sur les appuis d'une poutre sous cour",
            ),
            E("h2", "Suivi"),
            E(
                "body",
                "Les travaux de toiture et de renforcement ont été votés. L'étude de ventilation des caves reste à lancer.",
            ),
            E(
                "callout",
                "La répétition des infiltrations est cohérente avec les procès-verbaux 2024 et 2025.",
            ),
        ],
    ],
    "dtg_pppt": [
        [
            E("h1", "Méthode et limites de l'inspection"),
            E(
                "bullet",
                "Inspection visuelle des parties communes accessibles le 12/03/2026.",
            ),
            E(
                "bullet",
                "Absence de sondage destructif, de calcul de structure et d'analyse en laboratoire.",
            ),
            E(
                "bullet",
                "Toiture observée depuis une trappe et depuis la cour, sans échafaudage.",
            ),
            E(
                "bullet",
                "Deux caves encombrées n'ont pas été examinées sur toute leur surface.",
            ),
            E("bullet", "Les réseaux encastrés et fondations ne sont pas visibles."),
            E("h2", "Documents consultés"),
            E(
                "body",
                "Carnet d'entretien, procès-verbaux 2023 à 2025, factures de réparations et plans schématiques fournis par le syndic.",
            ),
        ],
        [
            E("h1", "Grille d'état par composant"),
            E("kv", "Charpente|État moyen, contrôle après dépose recommandé"),
            E("kv", "Couverture|État dégradé, priorité forte"),
            E("kv", "Façade rue|État moyen"),
            E("kv", "Façade cour|Fissures d'enduit, état dégradé"),
            E("kv", "Poutre sous cour|Corrosion des appuis, intervention prioritaire"),
            E("kv", "Réseaux d'eau|État moyen"),
            E("kv", "Escalier|État satisfaisant"),
            E("kv", "Ventilation des caves|Insuffisante"),
            E(
                "small",
                "Les qualificatifs sont propres à cette simulation et ne valent pas diagnostic d'ingénierie.",
            ),
        ],
    ],
    "dpe": [
        [
            E("h1", "Déperditions et confort"),
            E("lead", "Répartition conventionnelle issue du calcul synthétique"),
            E("kv", "Murs donnant sur l'extérieur|31 %"),
            E("kv", "Renouvellement d'air et ventilation|29 %"),
            E("kv", "Fenêtres et portes|18 %"),
            E("kv", "Ponts thermiques|15 %"),
            E("kv", "Plafond sous grenier|7 %"),
            E(
                "callout",
                "Performance de l'isolation : insuffisante. Confort d'été : insuffisant.",
            ),
            E(
                "body",
                "Le logement est traversant, mais les pièces sous rampant présentent un risque de surchauffe en période chaude.",
            ),
        ],
        [
            E("h1", "Montants et consommations annuelles"),
            E("kv", "Chauffage|5 980 kWh énergie finale, 70 % des dépenses"),
            E("kv", "Eau chaude sanitaire|1 630 kWh énergie finale, 19 %"),
            E("kv", "Éclairage|310 kWh énergie finale, 4 %"),
            E(
                "kv",
                "Auxiliaires et autres usages conventionnels|590 kWh énergie finale, 7 %",
            ),
            E("kv", "Total énergie finale|8 510 kWh/an"),
            E("kv", "Total énergie primaire|19 570 kWh/an"),
            E("kv", "Rapporté à la surface|302 kWh/m²/an"),
            E(
                "callout",
                "Fourchette de coûts conventionnels : 1 880 EUR à 2 650 EUR par an.",
            ),
        ],
        [
            E("h1", "Recommandations d'usage"),
            E(
                "bullet",
                "Maintenir une température de consigne de 19 °C en période de chauffe.",
            ),
            E(
                "bullet",
                "Ne pas obstruer les entrées d'air et nettoyer les grilles de ventilation.",
            ),
            E(
                "bullet",
                "Fermer les protections solaires pendant les heures chaudes en été.",
            ),
            E(
                "bullet",
                "Programmer le ballon d'eau chaude en heures creuses si le contrat le permet.",
            ),
            E(
                "bullet",
                "Adapter la durée des douches et surveiller les fuites d'eau chaude.",
            ),
            E("h2", "Limite"),
            E(
                "body",
                "Les consommations conventionnelles ne prédisent pas exactement les factures, qui dépendent de l'occupation, de la météo et des contrats d'énergie.",
            ),
        ],
        [
            E("h1", "Bouquet de travaux n° 1"),
            E("lead", "Actions prioritaires, montants indicatifs"),
            E("kv", "Régulation et remplacement de radiateurs|2 200 à 3 800 EUR"),
            E("kv", "Calfeutrement et entrées d'air adaptées|600 à 1 200 EUR"),
            E("kv", "Isolation ciblée du rampant accessible|4 500 à 7 500 EUR"),
            E("kv", "Montant total indicatif|7 300 à 12 500 EUR"),
            E(
                "callout",
                "Classe projetée après travaux : D, sous réserve d'une étude et de la réalisation conforme des travaux.",
            ),
            E(
                "body",
                "Les travaux sur l'enveloppe peuvent nécessiter l'accord de la copropriété et une coordination avec la réfection de toiture.",
            ),
        ],
        [
            E("h1", "Fiche technique du logement • enveloppe"),
            E("kv", "Mur nord|Pierre, environ 45 cm, isolation non observée"),
            E("kv", "Mur sud|Pierre, donnant sur rue, isolation non observée"),
            E("kv", "Plafond|Sous grenier partiellement aménagé"),
            E("kv", "Plancher bas|Sur logement chauffé"),
            E("kv", "Fenêtres|Double vitrage, cadres bois, pose déclarée en 2019"),
            E("kv", "Volets|Persiennes bois sur rue"),
            E("kv", "Orientation principale|Nord-sud"),
            E("kv", "Inertie|Lourde"),
            E(
                "small",
                "Origine des données : observation simulée et documents synthétiques fournis.",
            ),
        ],
        [
            E("h1", "Fiche technique du logement • systèmes"),
            E("kv", "Générateur de chauffage|Radiateurs électriques à effet Joule"),
            E("kv", "Années estimées des émetteurs|2008 à 2024 selon les pièces"),
            E("kv", "Régulation|Thermostats individuels, programmation partielle"),
            E("kv", "Eau chaude|Ballon électrique 150 litres, installé en 2020"),
            E("kv", "Ventilation|Conduits naturels, débits non mesurés"),
            E("kv", "Climatisation|Absente"),
            E("kv", "Énergie renouvelable|Aucun équipement individuel"),
            E("h2", "Point défavorable"),
            E(
                "body",
                "Le renouvellement d'air conventionnel contribue fortement aux déperditions et doit être traité sans supprimer la ventilation nécessaire.",
            ),
        ],
    ],
    "diagnostics": [
        [
            E("h1", "Détail du mesurage par pièce"),
            E("kv", "Entrée|4,10 m²"),
            E("kv", "Séjour|20,85 m²"),
            E("kv", "Cuisine|7,20 m²"),
            E("kv", "Chambre 1|10,70 m²"),
            E("kv", "Chambre 2|11,15 m²"),
            E("kv", "Salle d'eau|4,20 m²"),
            E("kv", "WC|1,35 m²"),
            E("kv", "Dégagement|1,95 m²"),
            E("kv", "Total Carrez|61,50 m²"),
            E(
                "small",
                "Grenier bas, embrasures et cave exclus. Sommes arrondies au centième.",
            ),
        ],
        [
            E("h1", "Amiante • objet et périmètre"),
            E(
                "bullet",
                "Mission limitée aux matériaux des listes réglementaires accessibles sans destruction.",
            ),
            E(
                "bullet",
                "Appartement, placards, faces visibles des conduits et cave accessible.",
            ),
            E(
                "bullet",
                "Parties communes hors mission, sauf traversées visibles depuis les lots.",
            ),
            E("bullet", "Aucun prélèvement destructif n'a été simulé."),
            E("h2", "Documents remis"),
            E(
                "body",
                "Plan schématique du lot, état descriptif de division et déclaration du propriétaire sur les travaux connus.",
            ),
        ],
        [
            E("h1", "Amiante • tableau de repérage"),
            E("kv", "Entrée, placard|Conduit fibrociment : amiante présumée présente"),
            E(
                "kv",
                "Cuisine|Dalles et colle : non repérées comme contenant de l'amiante",
            ),
            E("kv", "Salle d'eau|Plaques murales : non concernées"),
            E("kv", "Cave lot 42|Canalisations visibles : absence de matériau suspect"),
            E("kv", "État du conduit|Non dégradé"),
            E("kv", "Action|Évaluation périodique, ne pas percer ni poncer"),
            E(
                "callout",
                "Présence d'amiante maintenue comme constat principal du rapport.",
            ),
        ],
        [
            E("h1", "Plomb • stratégie de mesure"),
            E(
                "body",
                "Les revêtements peints accessibles sont répartis en unités de diagnostic par local, support et historique apparent.",
            ),
            E("kv", "Nombre d'unités simulées|74"),
            E("kv", "Mesures sous le seuil|69"),
            E("kv", "Mesures non concluantes|3"),
            E("kv", "Unités de classe 2|2"),
            E("kv", "Unités de classe 3|0"),
            E("h2", "Appareil"),
            E(
                "body",
                "Référence d'appareil volontairement omise. Aucune source radioactive ni aucun appareil réel n'a été utilisé.",
            ),
        ],
        [
            E("h1", "Plomb • résultats par unité"),
            E("kv", "Séjour, fenêtre nord, ouvrant gauche|1,4 mg/cm², classe 2"),
            E("kv", "Séjour, fenêtre nord, ouvrant droit|1,2 mg/cm², classe 2"),
            E("kv", "Chambre 1, plinthe est|0,3 mg/cm², classe 0"),
            E("kv", "Cuisine, porte|0,2 mg/cm², classe 0"),
            E("kv", "Entrée, huisserie|0,4 mg/cm², classe 0"),
            E(
                "callout",
                "Deux revêtements contiennent du plomb au-dessus du seuil. Ils sont en état d'usage, sans dégradation visible.",
            ),
            E(
                "body",
                "Le propriétaire est invité à surveiller l'état des peintures et à informer toute entreprise avant intervention.",
            ),
        ],
        [
            E("h1", "Électricité • synthèse des points contrôlés"),
            E("kv", "Appareil général de commande|Présent et accessible"),
            E("kv", "Protection différentielle|Incomplète sur deux circuits"),
            E("kv", "Protection contre surintensités|Présente"),
            E("kv", "Liaison équipotentielle salle d'eau|À vérifier après travaux"),
            E("kv", "Matériels vétustes|Présents dans le tableau secondaire"),
            E("kv", "Conducteurs non protégés|Non observés"),
            E("kv", "Prises avec terre|Présence hétérogène selon les pièces"),
            E(
                "callout",
                "L'installation intérieure d'électricité comporte des anomalies.",
            ),
        ],
        [
            E("h1", "Électricité • détail des anomalies"),
            E("h2", "Anomalie B3.3.6"),
            E(
                "body",
                "Deux circuits alimentant la salle d'eau ne sont pas protégés par un dispositif différentiel haute sensibilité adapté.",
            ),
            E("h2", "Anomalie B7.3"),
            E(
                "body",
                "Le tableau secondaire comporte un porte-fusible ancien dont une partie active peut devenir accessible après retrait du capot.",
            ),
            E("h2", "Mesures recommandées"),
            E("bullet", "Faire intervenir rapidement un électricien qualifié."),
            E(
                "bullet",
                "Ne pas déposer les capots et ne pas modifier l'installation avant sécurisation.",
            ),
        ],
        [
            E("h1", "Électricité • informations complémentaires"),
            E(
                "kv",
                "Année déclarée d'installation|Parties principales antérieures à 1995",
            ),
            E("kv", "Tableau principal|Entrée"),
            E("kv", "Tableau secondaire|Placard du dégagement"),
            E("kv", "Nombre de circuits repérés|11"),
            E("kv", "Nombre de prises testées|18"),
            E("kv", "Mesure de terre|Valeur non reproduite dans cette simulation"),
            E(
                "body",
                "Le diagnostic porte sur la sécurité des personnes. Il n'a pas pour objet d'attester la conformité complète de l'installation.",
            ),
        ],
        [
            E("h1", "Gaz • justification du classement sans objet"),
            E("bullet", "Aucun compteur individuel de gaz n'est associé au logement."),
            E(
                "bullet",
                "Aucune tuyauterie fixe de gaz n'est visible dans les pièces examinées.",
            ),
            E(
                "bullet",
                "Aucun appareil de cuisson, de chauffage ou d'eau chaude alimenté au gaz n'est déclaré.",
            ),
            E(
                "bullet",
                "Les anciennes traversées murales ne peuvent être qualifiées sans sondage.",
            ),
            E("h2", "Conclusion"),
            E(
                "body",
                "L'état de l'installation intérieure de gaz est classé sans objet sur la base du périmètre accessible et des déclarations synthétiques.",
            ),
        ],
        [
            E("h1", "Limites communes aux missions"),
            E("bullet", "Meubles lourds et éléments fixés non déplacés."),
            E("bullet", "Revêtements, doublages et gaines non déposés."),
            E("bullet", "Cave partiellement encombrée, visibilité estimée à 65 %."),
            E(
                "bullet",
                "Absence d'essai destructif et de démontage nécessitant un outil.",
            ),
            E(
                "bullet",
                "Installations communes exclues, sauf éléments directement visibles.",
            ),
            E(
                "body",
                "Toute modification, sinistre ou travaux ultérieurs peut rendre les conclusions obsolètes pour les zones concernées.",
            ),
        ],
        [
            E("h1", "Attestations et documents remis"),
            E(
                "kv",
                "Assurance professionnelle|Référence fictive, aucune police réelle",
            ),
            E(
                "kv",
                "Certification opérateur|Référence DEMO-CERT-001, sans existence réelle",
            ),
            E("kv", "Indépendance et impartialité|Déclaration synthétique"),
            E("kv", "Commande reçue|22/08/2026"),
            E("kv", "Visite simulée|25/08/2026"),
            E("kv", "Rapport édité|28/08/2026"),
            E("h2", "Annexes annoncées"),
            E(
                "body",
                "Croquis non coté, liste des locaux, modèle de conseils de sécurité et accusé de réception. Aucun de ces éléments ne constitue une preuve.",
            ),
        ],
    ],
    "erp_termites_bruit": [
        [
            E("h1", "Risques recensés dans le scénario"),
            E("kv", "Retrait-gonflement des argiles|Exposition faible"),
            E("kv", "Inondation|Non retenue pour la parcelle fictive"),
            E("kv", "Mouvement de terrain|Information communale, parcelle non ciblée"),
            E("kv", "Risque technologique|Non retenu"),
            E("kv", "Sismicité|Zone 2, faible"),
            E("kv", "Radon|Catégorie 1 dans le scénario"),
            E("kv", "Pollution des sols|Aucun secteur identifié dans le scénario"),
            E(
                "small",
                "Ces informations ne correspondent à aucune parcelle réelle et ne doivent pas être comparées à une adresse existante.",
            ),
        ],
        [
            E("h1", "Termites • zones examinées"),
            E("kv", "Appartement|Plinthes et huisseries accessibles, aucun indice"),
            E("kv", "Plancher séjour|Sondage visuel et sonore simulé, aucun indice"),
            E("kv", "Cave|Inspection partielle, aucun indice dans la zone visible"),
            E("kv", "Charpente commune|Hors mission"),
            E("h2", "Limite importante"),
            E(
                "callout",
                "Environ 35 % des parois et bois de la cave étaient masqués par des objets dans le scénario.",
            ),
            E(
                "body",
                "Un nouvel examen après dégagement est recommandé avant toute intervention sur les bois de la cave.",
            ),
        ],
        [
            E("h1", "Déclarations du vendeur fictif"),
            E("kv", "Indemnisation catastrophe naturelle|Aucune déclarée"),
            E("kv", "Sinistre technologique|Aucun déclaré"),
            E("kv", "Infestation de termites connue|Aucune déclarée"),
            E("kv", "Présence de mérule connue dans le lot|Aucune déclarée"),
            E("kv", "Travaux prescrits par un plan de risques|Aucun déclaré"),
            E("h2", "Réserves"),
            E(
                "body",
                "Les déclarations d'une personne fictive ne remplacent pas une interrogation des bases et arrêtés applicables à une adresse réelle.",
            ),
        ],
    ],
    "taxe_fonciere": [
        [
            E("h1", "Détail simulé du calcul"),
            E("kv", "Base nette communale|3 460 EUR"),
            E("kv", "Cotisation bâtie simulée|1 084 EUR"),
            E("kv", "Base enlèvement des ordures|1 960 EUR"),
            E("kv", "Cotisation ordures ménagères|196 EUR"),
            E("kv", "Frais de gestion simulés|Inclus"),
            E("kv", "Montant total|1 280 EUR"),
            E(
                "small",
                "Les bases, taux et libellés sont inventés. Aucun calcul fiscal réel ne peut être déduit de cette page.",
            ),
        ],
        [
            E("h1", "Références et paiement"),
            E("kv", "Numéro fiscal|Masqué, aucun identifiant réel"),
            E("kv", "Référence de l'avis|TF-DEMO-2026-001"),
            E("kv", "Adresse d'imposition|24 rue des Tisseurs, 69004 Lyon"),
            E("kv", "Mode de paiement|Information non reproduite"),
            E("kv", "Échéance simulée|15/10/2026"),
            E("h2", "Important"),
            E(
                "body",
                "La taxe foncière est fournie comme repère budgétaire. Sa répartition éventuelle lors d'une vente relève des stipulations de l'acte.",
            ),
        ],
    ],
    "cil": [
        [
            E("h1", "Caractéristiques des équipements"),
            E("kv", "Fenêtres|Bois double vitrage, pose déclarée en 2019"),
            E("kv", "Radiateurs séjour|Deux appareils de 1 500 W"),
            E("kv", "Radiateurs chambres|Deux appareils de 1 000 W"),
            E("kv", "Ballon d'eau chaude|150 litres, vertical mural"),
            E("kv", "Tableau électrique|Principal et secondaire"),
            E("kv", "Détecteur de fumée|Présence déclarée"),
            E("kv", "Robinet d'arrêt d'eau|Placard de l'entrée"),
            E(
                "small",
                "Références de fabricants et numéros de série volontairement omis.",
            ),
        ],
        [
            E("h1", "Entretien et recommandations déclaratives"),
            E(
                "bullet",
                "Détartrage du ballon déclaré en janvier 2025, facture non fournie.",
            ),
            E("bullet", "Nettoyage annuel des entrées d'air déclaré par l'occupant."),
            E("bullet", "Réglage d'une fenêtre de la chambre 2 déclaré en mars 2026."),
            E("bullet", "Aucune facture d'isolation du rampant n'a été retrouvée."),
            E("h2", "Documents à conserver"),
            E(
                "body",
                "Factures, notices, attestations d'entretien et autorisations de copropriété relatives aux futurs travaux.",
            ),
        ],
    ],
    "titre_propriete": [
        [
            E("h1", "Origine de propriété antérieure"),
            E(
                "body",
                "Pour les besoins du scénario, le bien est présenté comme provenant d'une vente reçue en 2006, puis d'une mutation en 2018 au profit de la propriétaire fictive.",
            ),
            E("kv", "Mutation précédente|18/05/2006, référence fictive"),
            E("kv", "Mutation actuelle|09/11/2018, référence fictive"),
            E(
                "kv",
                "Service de publicité foncière|Mention volontairement non exploitable",
            ),
            E("kv", "Prix historique|Non reproduit"),
            E("h2", "État civil"),
            E(
                "body",
                "Toutes les données d'état civil autres que le nom fictif sont supprimées afin que le fichier ne puisse pas être confondu avec un acte authentique.",
            ),
        ],
        [
            E("h1", "Désignation cadastrale et urbanisme"),
            E("kv", "Section|DEMO"),
            E("kv", "Numéro|0042"),
            E("kv", "Contenance|Valeur non opposable"),
            E("kv", "Destination déclarée|Habitation"),
            E("kv", "Droit de préemption|À vérifier dans tout dossier réel"),
            E("kv", "Alignement|À vérifier dans tout dossier réel"),
            E("h2", "Avertissement"),
            E(
                "body",
                "La désignation cadastrale n'identifie aucun terrain réel. Elle sert uniquement à fournir du texte documentaire au pipeline de démonstration.",
            ),
        ],
    ],
    "notice_copro": [
        [
            E("h1", "Assemblée générale et contestation"),
            E(
                "bullet",
                "La convocation présente l'ordre du jour et les pièces nécessaires aux décisions.",
            ),
            E(
                "bullet",
                "Les résolutions sont votées selon les majorités correspondant à leur objet.",
            ),
            E(
                "bullet",
                "Le procès-verbal retrace le résultat des votes et est notifié selon la situation des copropriétaires.",
            ),
            E(
                "bullet",
                "Les délais et conditions de contestation doivent être vérifiés dans les textes applicables et avec un professionnel.",
            ),
            E("h2", "Conseil syndical"),
            E(
                "body",
                "Le conseil syndical contrôle la gestion, prépare certaines décisions et rend compte à l'assemblée.",
            ),
        ],
        [
            E("h1", "Budget, charges et fonds travaux"),
            E(
                "bullet",
                "Le budget prévisionnel finance les dépenses courantes de maintenance et d'administration.",
            ),
            E(
                "bullet",
                "Les travaux hors budget font généralement l'objet de décisions et d'appels distincts.",
            ),
            E(
                "bullet",
                "Le fonds travaux est attaché au lot selon les règles applicables et les stipulations de la vente.",
            ),
            E(
                "bullet",
                "Les impayés de certains copropriétaires peuvent affecter la trésorerie collective.",
            ),
            E("h2", "Lecture du dossier"),
            E(
                "body",
                "Les comptes, appels de fonds, procès-verbaux et informations préalables doivent être rapprochés pour éviter les doubles comptes et identifier les échéances.",
            ),
        ],
    ],
}


DOCUMENTS = [
    replace(
        document,
        pages=(
            PREFIX_PAGES.get(document.logical_id, [])
            + document.pages
            + EXTRA_PAGES.get(document.logical_id, [])
        ),
    )
    for document in DOCUMENTS
]


def pdf_escape(value: str) -> str:
    encoded = value.encode("cp1252", errors="replace")
    result: list[str] = []
    for byte in encoded:
        if byte in (40, 41, 92):
            result.append("\\" + chr(byte))
        elif byte < 32 or byte > 126:
            result.append(f"\\{byte:03o}")
        else:
            result.append(chr(byte))
    return "".join(result)


def wrap_text(value: str, width: int) -> list[str]:
    return textwrap.wrap(
        value,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
        replace_whitespace=True,
    ) or [""]


def text_command(
    x: float, y: float, value: str, *, font: str, size: float, color: str
) -> str:
    return f"BT /{font} {size:.1f} Tf {color} rg {x:.1f} {y:.1f} Td ({pdf_escape(value)}) Tj ET"


def filled_rect(x: float, y: float, width: float, height: float, color: str) -> str:
    return f"{color} rg {x:.1f} {y:.1f} {width:.1f} {height:.1f} re f"


def stroked_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    color: str,
    line_width: float = 1,
) -> str:
    return (
        f"{color} RG {line_width:.1f} w "
        f"{x:.1f} {y:.1f} {width:.1f} {height:.1f} re S"
    )


def filled_arrow(x: float, y: float, width: float, height: float, color: str) -> str:
    point = min(12.0, width * 0.22)
    return (
        f"{color} rg {x:.1f} {y:.1f} m "
        f"{x + width - point:.1f} {y:.1f} l "
        f"{x + width:.1f} {y + height / 2:.1f} l "
        f"{x + width - point:.1f} {y + height:.1f} l "
        f"{x:.1f} {y + height:.1f} l h f"
    )


DPE_COLORS = {
    "mint": "0.89 0.95 0.92",
    "green": "0.00 0.66 0.47",
    "dark_green": "0.00 0.48 0.35",
    "pink": "0.92 0.05 0.42",
    "light_blue": "0.59 0.83 0.95",
    "text": "0.08 0.12 0.11",
    "muted": "0.38 0.45 0.42",
}

DPE_ENERGY_SCALE = [
    ("A", "0.15 0.68 0.39"),
    ("B", "0.29 0.71 0.32"),
    ("C", "0.58 0.76 0.28"),
    ("D", "0.97 0.86 0.05"),
    ("E", "0.98 0.69 0.03"),
    ("F", "0.94 0.34 0.08"),
    ("G", "0.82 0.08 0.08"),
]

DPE_GHG_COLORS = [
    "0.70 0.86 0.96",
    "0.55 0.74 0.88",
    "0.42 0.59 0.75",
    "0.34 0.43 0.62",
    "0.27 0.30 0.49",
    "0.22 0.20 0.39",
    "0.17 0.11 0.31",
]


def append_wrapped_text(
    commands: list[str],
    x: float,
    y: float,
    value: str,
    *,
    width: int,
    font: str,
    size: float,
    color: str,
    leading: float,
) -> float:
    for line in wrap_text(value, width):
        commands.append(text_command(x, y, line, font=font, size=size, color=color))
        y -= leading
    return y


def render_dpe_cover_page(document: DemoDocument, page_number: int, total: int) -> bytes:
    """Render the recognizable first page of a post-2021 French DPE.

    The layout deliberately resembles the standardized information hierarchy, while
    the bright simulation banner, fake identifier and absent logo prevent it from
    being mistaken for an issued diagnostic.
    """

    mint = DPE_COLORS["mint"]
    green = DPE_COLORS["green"]
    dark_green = DPE_COLORS["dark_green"]
    pink = DPE_COLORS["pink"]
    text = DPE_COLORS["text"]
    muted = DPE_COLORS["muted"]
    commands = [
        filled_rect(0, 0, 595, 842, "1 1 1"),
        filled_rect(14, 20, 567, 808, mint),
        filled_rect(332, 808, 239, 24, pink),
        text_command(
            343,
            816,
            "EXEMPLE DE DPE • DONNÉES ENTIÈREMENT FICTIVES",
            font="F2",
            size=7.5,
            color="1 1 1",
        ),
        filled_rect(27, 742, 541, 66, "1 1 1"),
        text_command(39, 771, "DPE", font="F2", size=32, color=green),
        text_command(
            118,
            787,
            "diagnostic de performance",
            font="F2",
            size=13.2,
            color=text,
        ),
        text_command(118, 770, "énergétique", font="F2", size=13.2, color=text),
        text_command(208, 770, "(logement)", font="F1", size=6.4, color=text),
        text_command(
            441,
            791,
            "n° : DEMO-DPE-LYON-001",
            font="F1",
            size=6.4,
            color=dark_green,
        ),
        text_command(
            464,
            778,
            "établi le : 25/08/2026",
            font="F1",
            size=6.4,
            color=dark_green,
        ),
        text_command(
            448,
            765,
            "valable jusqu'au : 24/08/2036",
            font="F2",
            size=6.4,
            color=dark_green,
        ),
        text_command(
            39,
            750,
            "Ce document simulé décrit la performance énergétique d'un logement fictif.",
            font="F1",
            size=6.3,
            color=dark_green,
        ),
        filled_rect(27, 648, 541, 86, "1 1 1"),
        filled_rect(39, 658, 174, 66, "0.83 0.85 0.84"),
        text_command(
            74,
            688,
            "photo du bien non fournie",
            font="F3",
            size=9,
            color="1 1 1",
        ),
        text_command(225, 714, "adresse :", font="F1", size=6.8, color=muted),
        text_command(
            272,
            714,
            "24 rue des Tisseurs, 69004 Lyon",
            font="F2",
            size=6.8,
            color=text,
        ),
        text_command(225, 701, "type de bien :", font="F1", size=6.8, color=muted),
        text_command(285, 701, "appartement", font="F2", size=6.8, color=text),
        text_command(225, 688, "année de construction :", font="F1", size=6.8, color=muted),
        text_command(325, 688, "1898", font="F2", size=6.8, color=text),
        text_command(225, 675, "surface habitable :", font="F1", size=6.8, color=muted),
        text_command(310, 675, "64,80 m²", font="F2", size=6.8, color=text),
        text_command(225, 662, "lot principal :", font="F1", size=6.8, color=muted),
        text_command(288, 662, "n° 18", font="F2", size=6.8, color=text),
        filled_rect(27, 307, 541, 333, "1 1 1"),
        filled_rect(31, 613, 533, 22, green),
        text_command(
            37,
            620,
            "Performance énergétique et climatique",
            font="F2",
            size=10.5,
            color="1 1 1",
        ),
        text_command(
            141,
            591,
            "logement extrêmement performant",
            font="F1",
            size=5.3,
            color=dark_green,
        ),
    ]

    chart_x = 146.0
    chart_y = 553.0
    for index, (grade, color) in enumerate(DPE_ENERGY_SCALE):
        row_y = chart_y - index * 27
        width = 45 + index * 13
        if grade == "E":
            commands.append(stroked_rect(chart_x - 4, row_y - 4, width + 8, 26, color=text, line_width=1.5))
        commands.append(filled_arrow(chart_x, row_y, width, 18, color))
        commands.append(
            text_command(chart_x + 7, row_y + 4, grade, font="F2", size=13, color="1 1 1")
        )

    commands.extend(
        [
            text_command(56, 485, "consommation", font="F1", size=5.3, color=muted),
            text_command(59, 476, "énergie primaire", font="F1", size=5.3, color=muted),
            stroked_rect(54, 441, 47, 33, color="0.20 0.20 0.20", line_width=1),
            text_command(61, 453, "302", font="F2", size=16, color=text),
            text_command(59, 444, "kWh/m²/an", font="F1", size=5.2, color=text),
            text_command(105, 485, "émissions", font="F1", size=5.3, color=muted),
            stroked_rect(104, 441, 39, 33, color="0.20 0.20 0.20", line_width=1),
            text_command(113, 453, "9", font="F2", size=16, color=text),
            text_command(108, 444, "kg CO2/m²/an", font="F1", size=4.6, color=text),
            text_command(145, 359, "logement extrêmement consommateur d'énergie", font="F1", size=5.1, color="0.72 0.05 0.05"),
            stroked_rect(363, 397, 155, 181, color=DPE_COLORS["light_blue"], line_width=1.3),
            text_command(374, 561, "dont émissions de gaz", font="F2", size=7.2, color=text),
            text_command(374, 550, "à effet de serre", font="F2", size=7.2, color=text),
            text_command(374, 530, "peu d'émissions de CO2", font="F1", size=5.2, color="0.26 0.63 0.82"),
        ]
    )
    ghg_x = 377.0
    ghg_y = 508.0
    for index, ((grade, _), color) in enumerate(zip(DPE_ENERGY_SCALE, DPE_GHG_COLORS)):
        row_y = ghg_y - index * 17
        width = 29 + index * 8
        commands.append(filled_arrow(ghg_x, row_y, width, 11, color))
        commands.append(
            text_command(ghg_x + 4, row_y + 2, grade, font="F2", size=7, color="1 1 1")
        )
        if grade == "B":
            commands.append(text_command(ghg_x + width + 7, row_y + 2, "9 kg CO2/m²/an", font="F2", size=6.2, color=text))
    commands.extend(
        [
            text_command(374, 407, "émissions de CO2 très importantes", font="F1", size=5.0, color="0.16 0.11 0.28"),
            filled_rect(44, 319, 219, 38, green),
            text_command(52, 343, "La classe énergétique dépend de la consommation", font="F2", size=5.7, color="1 1 1"),
            text_command(52, 333, "et des émissions. La plus défavorable est retenue.", font="F1", size=5.7, color="1 1 1"),
            text_command(52, 323, "Ici, le logement simulé est classé E.", font="F1", size=5.7, color="1 1 1"),
            filled_rect(365, 319, 165, 38, green),
            text_command(373, 341, "Ce logement émet 583 kg de CO2 par an", font="F2", size=5.7, color="1 1 1"),
            text_command(373, 330, "selon le calcul conventionnel fictif.", font="F1", size=5.7, color="1 1 1"),
            filled_rect(27, 176, 541, 121, "1 1 1"),
            filled_rect(31, 270, 533, 22, pink),
            text_command(37, 277, "Estimation des coûts annuels d'énergie du logement", font="F2", size=10.5, color="1 1 1"),
            text_command(39, 253, "Usages conventionnels : chauffage, eau chaude, éclairage et auxiliaires.", font="F1", size=6.0, color=muted),
            text_command(215, 218, "entre", font="F1", size=7, color=text),
            text_command(252, 212, "1 880 €", font="F2", size=17, color=text),
            text_command(327, 218, "et", font="F1", size=7, color=text),
            text_command(351, 212, "2 650 €", font="F2", size=17, color=text),
            text_command(426, 218, "par an", font="F1", size=7, color=text),
            "0.75 0.75 0.75 RG 0.8 w 170 198 m 454 198 l S",
            text_command(221, 184, "Prix de l'énergie retenus pour cette simulation", font="F1", size=5.5, color=muted),
            filled_rect(27, 66, 541, 100, "1 1 1"),
            text_command(39, 150, "Informations du diagnostiqueur simulé", font="F2", size=7.2, color=text),
            text_command(39, 134, "DIAGNOSTICS DÉMO RHÔNE", font="F2", size=7.2, color=text),
            text_command(39, 120, "24 rue Exemple, 69000 Lyon", font="F1", size=6.5, color=text),
            text_command(39, 106, "Opérateur : Morgan Vidal (identité fictive)", font="F1", size=6.5, color=text),
            text_command(252, 134, "tél. : non attribué", font="F1", size=6.5, color=muted),
            text_command(252, 120, "certification : DEMO-CERT-001", font="F1", size=6.5, color=muted),
            text_command(252, 106, "assurance : référence fictive", font="F1", size=6.5, color=muted),
            stroked_rect(458, 94, 85, 48, color="0.72 0.75 0.73", line_width=1),
            text_command(473, 113, "AUCUN LOGO", font="F2", size=8, color=muted),
            text_command(481, 101, "NI SIGNATURE", font="F2", size=7, color=muted),
            text_command(39, 78, "Rapport généré pour tester Acquora. Aucun diagnostic, visite ou certification réels.", font="F3", size=5.8, color=muted),
            filled_rect(27, 34, 541, 22, pink),
            text_command(93, 42, DEMO_NOTICE, font="F2", size=7.3, color="1 1 1"),
            text_command(548, 24, f"{page_number}/{total}", font="F1", size=6, color=muted),
        ]
    )

    stream = "\n".join(commands).encode("latin-1")
    return zlib.compress(stream, level=9)


def render_dpe_detail_page(
    document: DemoDocument, elements: list[Element], page_number: int, total: int
) -> bytes:
    """Render subsequent DPE pages in the same green and pink visual system."""

    green = DPE_COLORS["green"]
    dark_green = DPE_COLORS["dark_green"]
    pink = DPE_COLORS["pink"]
    text = DPE_COLORS["text"]
    muted = DPE_COLORS["muted"]
    commands = [
        filled_rect(0, 0, 595, 842, "1 1 1"),
        filled_rect(14, 20, 567, 808, DPE_COLORS["mint"]),
        filled_rect(332, 808, 239, 24, pink),
        text_command(343, 816, "EXEMPLE DE DPE • DONNÉES ENTIÈREMENT FICTIVES", font="F2", size=7.5, color="1 1 1"),
        filled_rect(27, 754, 541, 48, "1 1 1"),
        text_command(39, 771, "DPE", font="F2", size=24, color=green),
        text_command(100, 781, "diagnostic de performance énergétique", font="F2", size=10.5, color=text),
        text_command(100, 766, "24 rue des Tisseurs, 69004 Lyon • DEMO-DPE-LYON-001", font="F1", size=6.3, color=dark_green),
        text_command(535, 766, f"{page_number}/{total}", font="F2", size=7, color=dark_green),
        filled_rect(27, 54, 541, 690, "1 1 1"),
        filled_rect(27, 34, 541, 16, pink),
        text_command(133, 39, "DOCUMENT SIMULÉ • SANS VALEUR CONTRACTUELLE", font="F2", size=6.8, color="1 1 1"),
    ]
    y = 712.0
    first_heading = True
    row_index = 0

    for kind, value in elements:
        if kind == "space":
            y -= 10
            continue
        if kind == "h1":
            if first_heading:
                commands.append(filled_rect(31, y - 5, 533, 25, green))
                commands.append(text_command(38, y + 3, value, font="F2", size=11.2, color="1 1 1"))
                y -= 39
                first_heading = False
            else:
                y -= 5
                commands.append(text_command(39, y, value, font="F2", size=15, color=text))
                y -= 25
        elif kind == "lead":
            y = append_wrapped_text(commands, 39, y, value, width=82, font="F3", size=9, color=muted, leading=13)
            y -= 7
        elif kind == "h2":
            y -= 4
            commands.append(filled_rect(39, y - 4, 513, 20, "0.91 0.96 0.93"))
            commands.append(text_command(45, y + 2, value, font="F2", size=9.4, color=dark_green))
            y -= 29
        elif kind == "body":
            y = append_wrapped_text(commands, 45, y, value, width=91, font="F1", size=8.7, color=text, leading=13)
            y -= 7
        elif kind == "bullet":
            lines = wrap_text(value, 84)
            commands.append(filled_rect(46, y + 2, 5, 5, green))
            for line in lines:
                commands.append(text_command(59, y, line, font="F1", size=8.7, color=text))
                y -= 13
            y -= 5
        elif kind == "kv":
            label, _, item_value = value.partition("|")
            label_lines = wrap_text(label, 31)
            value_lines = wrap_text(item_value, 51)
            row_lines = max(len(label_lines), len(value_lines))
            row_height = 13 * row_lines + 10
            if row_index % 2 == 0:
                commands.append(filled_rect(39, y - row_height + 8, 513, row_height, "0.95 0.97 0.96"))
            for index, line in enumerate(label_lines):
                commands.append(text_command(47, y - index * 13, line, font="F2", size=8.2, color=dark_green))
            for index, line in enumerate(value_lines):
                commands.append(text_command(239, y - index * 13, line, font="F1", size=8.5, color=text))
            y -= row_height
            row_index += 1
        elif kind == "callout":
            lines = wrap_text(value, 78)
            height = 14 * len(lines) + 18
            commands.append(filled_rect(39, y - height + 8, 513, height, green))
            for index, line in enumerate(lines):
                commands.append(text_command(51, y - index * 14, line, font="F2", size=8.8, color="1 1 1"))
            y -= height + 7
        elif kind == "small":
            y -= 2
            y = append_wrapped_text(commands, 45, y, value, width=102, font="F3", size=7.1, color=muted, leading=10)
            y -= 3

        if y < 68:
            raise ValueError(f"DPE page overflow in {document.filename}, page {page_number}")

    stream = "\n".join(commands).encode("latin-1")
    return zlib.compress(stream, level=9)


def render_page(
    document: DemoDocument, elements: list[Element], page_number: int, total: int
) -> bytes:
    if document.logical_id == "dpe":
        if page_number == 1:
            return render_dpe_cover_page(document, page_number, total)
        return render_dpe_detail_page(document, elements, page_number, total)

    commands = [
        "1 1 1 rg 0 0 595 842 re f",
        "0.08 0.08 0.08 rg 0 800 595 42 re f",
        text_command(
            34, 816, document.title.upper(), font="F2", size=8.2, color="1 1 1"
        ),
        text_command(
            561,
            816,
            f"{page_number}/{total}",
            font="F1",
            size=8,
            color="0.82 0.82 0.82",
        ),
        "0.91 0.91 0.91 rg 0 0 595 28 re f",
        text_command(34, 10, DEMO_NOTICE, font="F2", size=7.2, color="0.18 0.18 0.18"),
    ]
    y = 763.0

    for kind, value in elements:
        if kind == "space":
            y -= 10
            continue
        if kind == "h1":
            for line in wrap_text(value, 44):
                commands.append(
                    text_command(
                        34, y, line, font="F2", size=19, color="0.07 0.07 0.07"
                    )
                )
                y -= 23
            y -= 5
        elif kind == "lead":
            for line in wrap_text(value, 74):
                commands.append(
                    text_command(
                        34, y, line, font="F3", size=10.5, color="0.32 0.32 0.32"
                    )
                )
                y -= 15
            y -= 9
        elif kind == "h2":
            y -= 7
            commands.append(f"0.42 0.42 0.42 RG 34 {y + 13:.1f} m 561 {y + 13:.1f} l S")
            for line in wrap_text(value, 64):
                commands.append(
                    text_command(
                        34, y, line, font="F2", size=11.3, color="0.10 0.10 0.10"
                    )
                )
                y -= 16
            y -= 2
        elif kind == "body":
            for line in wrap_text(value, 91):
                commands.append(
                    text_command(
                        34, y, line, font="F1", size=9.2, color="0.16 0.16 0.16"
                    )
                )
                y -= 13
            y -= 5
        elif kind == "bullet":
            lines = wrap_text(value, 85)
            commands.append(
                text_command(39, y, "•", font="F2", size=10, color="0.18 0.18 0.18")
            )
            for index, line in enumerate(lines):
                commands.append(
                    text_command(
                        52, y, line, font="F1", size=9.2, color="0.16 0.16 0.16"
                    )
                )
                y -= 13
            y -= 3
        elif kind == "kv":
            label, _, item_value = value.partition("|")
            label_lines = wrap_text(label, 30)
            value_lines = wrap_text(item_value, 54)
            row_lines = max(len(label_lines), len(value_lines))
            row_height = 13 * row_lines + 11
            commands.append(
                f"0.94 0.94 0.94 rg 34 {y - row_height + 7:.1f} 527 {row_height:.1f} re f"
            )
            for index, line in enumerate(label_lines):
                commands.append(
                    text_command(
                        43,
                        y - index * 13,
                        line,
                        font="F2",
                        size=8.7,
                        color="0.20 0.20 0.20",
                    )
                )
            for index, line in enumerate(value_lines):
                commands.append(
                    text_command(
                        232,
                        y - index * 13,
                        line,
                        font="F1",
                        size=9,
                        color="0.10 0.10 0.10",
                    )
                )
            y -= row_height
        elif kind == "callout":
            lines = wrap_text(value, 79)
            height = 14 * len(lines) + 21
            commands.append(
                f"0.88 0.88 0.88 rg 34 {y - height + 8:.1f} 527 {height:.1f} re f"
            )
            commands.append(
                f"0.18 0.18 0.18 rg 34 {y - height + 8:.1f} 4 {height:.1f} re f"
            )
            for index, line in enumerate(lines):
                commands.append(
                    text_command(
                        48,
                        y - index * 14,
                        line,
                        font="F2",
                        size=9.3,
                        color="0.10 0.10 0.10",
                    )
                )
            y -= height + 5
        elif kind == "small":
            y -= 3
            for line in wrap_text(value, 104):
                commands.append(
                    text_command(
                        34, y, line, font="F3", size=7.6, color="0.38 0.38 0.38"
                    )
                )
                y -= 11
            y -= 2

        if y < 46:
            raise ValueError(
                f"Page overflow in {document.filename}, page {page_number}"
            )

    stream = "\n".join(commands).encode("latin-1")
    return zlib.compress(stream, level=9)


def build_pdf(document: DemoDocument) -> bytes:
    objects: list[bytes] = []

    def add_object(value: bytes) -> int:
        objects.append(value)
        return len(objects)

    catalog_id = add_object(b"")
    pages_id = add_object(b"")
    regular_font_id = add_object(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )
    bold_font_id = add_object(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    )
    italic_font_id = add_object(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>"
    )
    info_id = add_object(
        (
            "<< "
            f"/Title ({pdf_escape(document.title)}) "
            "/Author (Générateur de documents synthétiques) "
            "/Subject (Dossier immobilier synthétique de démonstration) "
            "/Keywords (démonstration, document synthétique, Lyon) "
            ">>"
        ).encode("latin-1")
    )

    page_ids: list[int] = []
    for page_number, elements in enumerate(document.pages, start=1):
        compressed = render_page(document, elements, page_number, len(document.pages))
        stream_id = add_object(
            f"<< /Length {len(compressed)} /Filter /FlateDecode >>\nstream\n".encode()
            + compressed
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {regular_font_id} 0 R /F2 {bold_font_id} 0 R "
                f"/F3 {italic_font_id} 0 R >> >> /Contents {stream_id} 0 R >>"
            ).encode()
        )
        page_ids.append(page_id)

    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = (
        f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode()
    )

    output = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(output)


def build_manifest(generated: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "fixture_kind": "synthetic_demo_dossier",
        "case": {
            "title": f"{DEMO_ADDRESS} • Démo",
            "property_type": "apartment_coproperty",
            "price_eur": "395000.00",
            "surface_m2": "64.80",
            "lot_count": 2,
            "address_is_fictional": True,
            "read_only": True,
        },
        "scenario": {
            "summary": "Appartement ancien en copropriété avec dossier complet et plusieurs points de vigilance documentés.",
            "expected_signals": [
                "DPE E, 302 kWh/m²/an et estimation haute de 2 650 EUR/an",
                "écart de 3,30 m² entre surface DPE (64,80 m²) et Carrez (61,50 m²)",
                "réfection de toiture votée pour 96 000 EUR, quote-part de 6 960 EUR",
                "trois appels travaux futurs de 2 320 EUR",
                "renforcement structurel voté pour 42 000 EUR, quote-part de 3 045 EUR",
                "hausse des charges individuelles de 1 780 EUR à 2 980 EUR",
                "21 600 EUR d'impayés à l'échelle de la copropriété",
                "infiltrations de toiture mentionnées en 2024 et 2025",
                "contentieux amiable en cours pour 18 500 EUR",
                "amiante localisée et non dégradée, plomb de classe 2",
                "anomalies électriques explicites",
                "état termites négatif avec limite d'inspection de la cave",
            ],
            "expected_missing_document_findings": [],
        },
        "documents": generated,
        "sources_used_to_scope_the_fixture": [
            "https://www.anil.org/votre-besoin/gerer-un-bien/copropriete/devenir-proprietaire-achat-dun-logement-en-copropriete/",
            "https://www.anil.org/aj-copropriete-fiche-synthetique/",
            "https://www.rhone.gouv.fr/Actions-de-l-Etat/Amenagement-du-territoire-urbanisme-construction-logement/Construction/Termites",
        ],
        "local_layout_references": {
            "files": [
                "data/22_bd_reuilly/DPE_D.pdf",
                "data/22_bd_reuilly/Diagnostics T3 22 Bd Reuilly.pdf",
            ],
            "use": "Structure visuelle et découpage des sections uniquement. Aucune donnée personnelle ou valeur du bien de référence n'est reprise.",
        },
        "generation": {
            "command": "python3 scripts/generate_demo_dossier.py",
            "notice": DEMO_NOTICE,
            "pdf_profile": "searchable text, built-in fonts, Flate-compressed streams",
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, object]] = []
    expected_filenames = {document.filename for document in DOCUMENTS}
    for stale in OUTPUT_DIR.glob("*.pdf"):
        if stale.name not in expected_filenames:
            stale.unlink()

    for document in DOCUMENTS:
        content = build_pdf(document)
        target = OUTPUT_DIR / document.filename
        target.write_bytes(content)
        generated.append(
            {
                "logical_id": document.logical_id,
                "filename": document.filename,
                "title": document.title,
                "classification_hint": document.classification_hint,
                "issuer": document.issuer,
                "document_date": document.document_date,
                "covered_period_start": document.covered_period_start,
                "covered_period_end": document.covered_period_end,
                "purpose": document.purpose,
                "page_count": len(document.pages),
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )

    manifest = build_manifest(generated)
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    total_size = sum(int(item["size_bytes"]) for item in generated)
    print(f"Generated {len(generated)} PDFs ({total_size} bytes) in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
