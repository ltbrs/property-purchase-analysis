"""Populate the ministry's apartment DPE specimen, without any private PDF input.

Coordinates are PDF points from the top left of the pinned September 2025 model.
Redactions remove old text, including hidden text, before inserting demo fields.
This is a presentation fixture, not a 3CL calculation or a certified diagnostic.
"""

from pathlib import Path
import hashlib

import pymupdf as fitz

TEMPLATE = Path(__file__).with_name("assets") / "dpe-appartement-officiel-2025.pdf"
TEMPLATE_URL = "https://rt-re-batiment.developpement-durable.gouv.fr/IMG/pdf/02_dpe_existant_appartement_01.09_2025.pdf"
TEMPLATE_SHA256 = "1e6096dc06030e5696aff1046acf279dab8b827703081778366a0520c0cd4131"
FONTS = {
    bold: fitz.Font(fontfile=str(TEMPLATE.parent / f"IBMPlexSans-{weight}.ttf"))
    for bold, weight in ((False, "Regular"), (True, "Bold"))
}
PAGE_TITLES = (
    "Performance énergétique et climatique",
    "Déperditions, isolation et confort d'été",
    "Montants, consommations et recommandations d'usage",
    "Vue d'ensemble du logement et des équipements",
    "Recommandations d'amélioration de la performance",
    "Évolution de la performance après travaux",
    "Annexe : fiche technique du logement",
    "Annexe : enveloppe et équipements",
)
NOTICE = "DOCUMENT SYNTHÉTIQUE DE DÉMONSTRATION • SANS VALEUR CONTRACTUELLE"
REFERENCE = "DEMO-DPE-LYON-001"
ADDRESS = "24 rue des Tisseurs, 69004 Lyon"
SURFACE = 64.8
# Coefficient applicable at the fixture's date, 25 August 2026.
ELECTRICITY_PRIMARY_FACTOR = 1.9
# final kWh, minimum EUR, maximum EUR, displayed share of expenditure.
USES = ((7240, 1320, 1855, 70), (1970, 355, 505, 19), (0, 0, 0, 0),
        (380, 75, 105, 4), (710, 130, 185, 7))
CLIMATE_COLORS = ("a4dfef", "8bb5d0", "7799b5", "606f93", "4d4d6b", "393550", "281e37")


def rgb(value):
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def number(value):
    return f"{value:,}".replace(",", " ")


def text(page, rect, value, size=9, bold=False, color=(0, 0, 0), align=0):
    """Fail on overflow instead of silently dropping text or shrinking it away."""
    rect = fitz.Rect(rect)
    font = FONTS[bold]
    fontname = "DemoBold" if bold else "DemoRegular"
    page.insert_font(fontname=fontname, fontbuffer=font.buffer)
    lines = []
    for paragraph in value.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if font.text_length(candidate, fontsize=size) > rect.width:
                if not line:
                    raise ValueError(f"DPE word too wide: {word!r}")
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    if len(lines) * size * 1.2 > rect.height + 0.01:
        raise ValueError(f"DPE page {page.number + 1}: text does not fit {rect}: {value!r}")
    for i, line in enumerate(lines):
        width = font.text_length(line, fontsize=size)
        x = rect.x0 + ((rect.width - width) / 2 if align == 1 else 0)
        page.insert_text((x, rect.y0 + size * (0.95 + i * 1.2)), line,
                         fontsize=size, fontname=fontname, color=color)


class Editor:
    def __init__(self, page):
        self.page = page
        self.fields = []

    def field(self, rect, value="", size=9, bold=False, color=(0, 0, 0), graphics=False):
        # Text-only redactions retain table backgrounds, rules and pictograms.
        self.page.add_redact_annot(fitz.Rect(rect), fill=False, cross_out=False)
        self.fields.append((rect, value, size, bold, color, graphics))

    def finish(self):
        self.page.apply_redactions(images=0, graphics=0)
        for rect, value, size, bold, color, graphics in self.fields:
            if graphics:
                self.page.add_redact_annot(fitz.Rect(rect), fill=(1, 1, 1), cross_out=False)
                self.page.apply_redactions(images=2, graphics=1)
            if value:
                text(self.page, rect, value, size, bold, color)


def climate_scale(page, x, y, width, step):
    """Update the climate scale from the specimen's E rating to the fixture's B."""
    for i, (grade, color) in enumerate(zip("ABCDEFG", CLIMATE_COLORS)):
        w, h = width * (0.42 + i * 0.095), step - 3
        r = fitz.Rect(x, y + i * step, x + w, y + i * step + h)
        page.draw_rect(r, color=(0, 0, 0) if grade == "B" else None,
                       fill=rgb(color), radius=0.45, width=1)
        text(page, (x + 4, r.y0 - 1, x + 30, r.y1 + 4), grade,
             size=min(18, h - 1), bold=True, color=(1, 1, 1))


def cover(page):
    e = Editor(page)
    e.field((343, 29, 563, 112),
            f"n° : {REFERENCE}\nétabli le : 25/08/2026\nvalable jusqu'au : 24/08/2036\nIdentifiant fictif, non enregistré à l'ADEME",
            8, color=rgb("009e7b"), graphics=True)
    e.field((37, 85, 340, 111), "Ce document présente la performance énergétique du logement fictif.\nInformations : ecologie.gouv.fr/diagnostic-performance-energetique-dpe", 6.4)
    e.field((225, 120, 558, 216),
            f"adresse : {ADDRESS} / 3e étage, lot 18\ntype de bien : appartement\nannée de construction : 1898\nsurface de référence : 64,80 m²\n\npropriétaire : Camille Bernard (personnage fictif)\nadresse : {ADDRESS}", 8.5)
    e.field((40, 130, 211, 205), "Logement fictif\nPhotographie non fournie", 12, color=rgb("777777"))
    e.field((57, 393, 98, 416), "302", 19, True)
    e.field((108, 393, 139, 416), "9*", 19, True)
    e.field((52, 435, 103, 456), "159 kWh/m²/an\nd'énergie finale", 6.6, color=rgb("777777"))
    e.field((390, 332, 534, 426), graphics=True)
    e.field((387, 487, 537, 545), "Ce logement émet 583 kg de CO2\npar an pour une surface de 64,80 m².\n\nLe niveau d'émissions dépend\nprincipalement des types d'énergies\nutilisées. Valeurs synthétiques.", 7, False, (1, 1, 1))
    e.field((223, 608, 292, 637), "1 880 €", 18, True)
    e.field((321, 608, 391, 637), "2 650 €", 18, True)
    e.field((36, 728, 560, 778), graphics=True)
    e.field((390, 713, 560, 782), graphics=True)
    e.field((32, 784, 560, 811),
            "Simulation documentaire : aucun diagnostic réalisé, aucune certification ni transmission à l'ADEME.\nMaquette nationale du ministère, modèle appartement de septembre 2025. Données du scénario lyonnais entièrement fictives.", 6)
    e.finish()
    climate_scale(page, 394, 334, 85, 13)
    text(page, (148, 499, 341, 511), "Classe énergie : E • Classe climat : B", 7, color=rgb("009e7b"))
    page.draw_line((451, 353), (475, 353), color=(0, 0, 0))
    text(page, (476, 346, 536, 365), "9 kg CO2/m²/an", 6.6, True)
    text(page, (37, 730, 212, 778), "Diagnostics Démo Rhône\n24 rue Exemple, 69000 Lyon\nDiagnostiqueur : Morgan Vidal\nIdentités et coordonnées fictives", 8)
    text(page, (215, 730, 430, 778), "Certification : DEMO-CERT-001 (fictive)\nAssurance : référence fictive\nContact : non attribué\nAucune signature ni certification réelle", 8)
    text(page, (440, 743, 553, 775), "SPÉCIMEN\nSANS SIGNATURE", 9, True, rgb("777777"))


def comfort(page):
    e = Editor(page)
    labels = [((78, 109, 127, 147), "ventilation", "29%", 122),
              ((210, 104, 257, 152), "toiture ou\nplafond", "7%", 131),
              ((237, 185, 283, 225), "murs", "31%", 201),
              ((47, 180, 96, 229), "portes\net fenêtres", "18%", 206),
              ((54, 264, 139, 302), "ponts thermiques", "15%", 279)]
    for rect, _, _, _ in labels:
        e.field(rect)
    e.field((380, 236, 555, 296), "Ventilation naturelle par conduits.\nDébits non mesurés.\n\nNe pas obstruer les entrées d'air.", 8.5)
    e.finish()
    for rect, label, value, y in labels:
        text(page, (rect[0], rect[1], rect[2], y), label, 8)
        text(page, (rect[0], y, rect[2], y + 24), value, 19, True)


def consumption(page):
    e = Editor(page)
    for y, (final, low, high, share) in zip((138, 166, 194, 222, 251), USES):
        e.field((150, y - 1, 291, y + 17),
                f"{'électrique' if final else ''}   {number(round(final * ELECTRICITY_PRIMARY_FACTOR))} ({number(final)} é.f.)", 7.6)
        e.field((303, y - 1, 404, y + 17), f"entre {number(low)} € et {number(high)} €" if final else "0 €", 7.6, True)
    e.field((198, 273, 291, 302), "19 570 kWh\n(10 300 kWh é.f.)", 9, True)
    e.field((303, 273, 404, 302), "1 880 € à 2 650 €\npar an", 9, True)
    e.field((411, 130, 558, 274), graphics=True)
    # Remove the oil boiler pictogram and sample-specific caveat as well.
    e.field((138, 138, 150, 150), graphics=True)
    e.field((34, 310, 297, 333), "Installation électrique individuelle. Montants synthétiques.\nConversion électricité : 1 kWh final = 1,9 kWh primaire.", 7, graphics=True)
    e.field((36, 336, 298, 382), "Hypothèses d'usage de la simulation : chauffage à 19 °C,\nréduit à 16 °C la nuit ou en cas d'absence.\nLe logement ne possède pas de climatisation.\nLes dépenses dépendent des usages et des contrats.", 8)
    e.field((81, 468, 362, 522))
    e.field((81, 635, 361, 738), "Eau chaude sanitaire\nBallon électrique individuel de 150 litres.\n\nAdapter la durée des douches et surveiller\nles fuites d'eau chaude.\nProgrammer le ballon selon le contrat\nd'électricité et les besoins du foyer.", 10)
    # The ministry file also contains an obsolete URL hidden under a later edit.
    e.field((100, 766, 357, 792))
    e.finish()
    text(page, (82, 469, 362, 487), "Température recommandée en hiver : 19 °C", 12, True)
    text(page, (82, 489, 362, 522), "Chauffer à 19 °C plutôt qu'à 21 °C\nréduit les dépenses de chauffage.", 12)
    text(page, (107, 768, 358, 792), "En savoir plus sur les économies d'énergie :\nfrance-renov.gouv.fr", 8.5, True, (1, 1, 1))
    for y, (_, _, _, share) in zip((133, 161, 189, 217, 245), USES):
        width = share * 1.3
        if width:
            page.draw_rect((413, y, 413 + width, y + 25), color=None, fill=rgb("e92d88"))
        text(page, (418 + width, y + 2, 565, y + 27), f"{share}%", 18, True)


def overview(page):
    # Remove the sample's oil-boiler warning icon before replacing its caption.
    page.add_redact_annot((161, 358, 170, 373), fill=rgb("f4f3f8"), cross_out=False)
    page.apply_redactions(images=0, graphics=1)
    e = Editor(page)
    for rect, value in [
        ((149, 143, 470, 189), "Murs nord et sud en pierre, environ 45 cm, donnant sur l'extérieur.\nIsolation non observée. Orientation principale nord-sud."),
        ((149, 196, 470, 213), "Plancher sur logement chauffé, sans déperdition conventionnelle."),
        ((149, 224, 470, 241), "Plafond sous grenier partiellement aménagé, isolation insuffisante."),
        ((149, 247, 470, 284), "Fenêtres à double vitrage, cadres bois, pose déclarée en 2019.\nPersiennes bois sur rue. Étanchéité à l'air à améliorer.\nPorte : caractéristiques thermiques non documentées."),
        ((160, 348, 554, 374), "Chauffage électrique individuel : radiateurs à effet Joule.\nÉmetteurs de 2008 à 2024 selon les pièces (hypothèse fictive)."),
        ((160, 382, 554, 399), "Ballon électrique individuel de 150 litres, installé en 2020."),
        ((160, 433, 554, 461), "Ventilation naturelle par conduits.\nDébits non mesurés."),
        ((160, 467, 554, 483), "Thermostats individuels, programmation partielle."),
        ((160, 576, 554, 602), "Ne pas obstruer les entrées d'air. Nettoyer les grilles régulièrement.\nAérer les pièces pour préserver la qualité de l'air intérieur."),
        ((67, 609, 149, 627), "programmation"),
        ((160, 610, 554, 627), "Adapter les horaires de chauffe à l'occupation du logement."),
        ((67, 666, 149, 683), "régulation"),
        ((160, 661, 554, 687), "Vérifier les thermostats individuels et leur fonctionnement.\nAucun circuit de chauffage à eau dans ce scénario."),
    ]:
        e.field(rect, value, 8)
    e.finish()


def recommendations(page):
    for y in (328, 406, 420, 614):
        page.add_redact_annot((176, y, 185, y + 14), fill=rgb("fff5ea"), cross_out=False)
    page.apply_redactions(images=0, graphics=1)
    e = Editor(page)
    e.field((88, 247, 550, 269), "Les travaux essentiels   montant estimé : 7 300 à 12 500 €", 12, True)
    e.field((88, 495, 550, 516), "Les travaux à envisager   montant : non chiffré", 12, True)
    for rect, value in [
        ((176, 304, 419, 342), "Isoler les rampants accessibles sous le grenier.\nBudget indicatif : 4 500 à 7 500 €.\nCoordonner avec la copropriété et la toiture."),
        ((424, 315, 552, 342), "Résistance thermique\nà définir par étude"),
        ((176, 344, 419, 379), "Aucune isolation des murs chiffrée dans ce pack.\nVérifier l'humidité avant toute intervention."),
        ((424, 353, 552, 378), "Non évaluée"),
        ((176, 381, 419, 437), "Améliorer l'étanchéité à l'air des menuiseries\nsans dégrader la ventilation.\nBudget indicatif : 600 à 1 200 €.\nAutorisations à vérifier avant intervention."),
        ((424, 399, 552, 430), "Préserver les\nentrées d'air"),
        ((176, 446, 419, 470), "Remplacer les radiateurs anciens et améliorer\nla régulation : 2 200 à 3 800 €."),
        ((424, 445, 552, 470), "Régulation\nélectronique"),
        ((177, 557, 419, 586), "Étudier l'amélioration de la production d'eau\nchaude après vérification de la faisabilité."),
        ((424, 563, 552, 588), "Non évaluée"),
        ((177, 589, 419, 632), "Étudier un système plus performant adapté\nau logement et aux règles de copropriété.\nAucun remplacement par une chaudière gaz."),
        ((424, 601, 552, 626), "Non évaluée"),
        ((177, 640, 419, 663), "Étudier une ventilation adaptée à l'enveloppe\net aux conduits existants."),
    ]:
        e.field(rect, value, 8)
    e.field((41, 715, 552, 786), "Montants fictifs, sans devis ni audit énergétique. Le pack 1 représente 7 300 à 12 500 €.\nGain indicatif envisagé : 45 à 60 kWh/m²/an, avec une classe D projetée sous réserve d'étude.\nLes travaux sur l'enveloppe peuvent nécessiter l'accord de la copropriété.\nAucune facture d'isolation des rampants n'est disponible dans le dossier.", 9)
    e.finish()


def projections(page):
    e = Editor(page)
    e.field((48, 165, 191, 354), graphics=True)
    e.field((73, 494, 194, 607), graphics=True)
    # Old lines must not continue to point at the sample's B/C/E ratings.
    e.field((184, 175, 193, 355), graphics=True)
    e.field((185, 480, 193, 608), graphics=True)
    e.finish()
    for rect, value, target in [
        ((53, 190, 166, 230), "Avec travaux 1 + 2\nPerformance non évaluée", None),
        ((53, 241, 166, 279), "Avec travaux 1 : classe D\n250 kWh/m²/an\n8 kg CO2/m²/an", (193, 266)),
        ((53, 289, 166, 328), "État actuel : classe E\n302 kWh/m²/an\n9 kg CO2/m²/an", (193, 295)),
        ((78, 497, 172, 528), "Avec travaux 1 + 2\nNon évalué", None),
        ((78, 537, 172, 568), "Avec travaux 1 : B\n8 kg CO2/m²/an", (193, 499)),
        ((78, 577, 172, 608), "État actuel : B\n9 kg CO2/m²/an", (193, 499)),
    ]:
        page.draw_rect(rect, color=(0, 0, 0), fill=(1, 1, 1), radius=0.08, width=0.8)
        text(page, (rect[0] + 4, rect[1] + 3, rect[2] - 3, rect[3]), value, 7.4)
        if target:
            page.draw_line((rect[2], (rect[1] + rect[3]) / 2), target, color=(0, 0, 0), width=0.8)
            page.draw_circle(target, 2, color=None, fill=(0, 0, 0))
    text(page, (40, 662, 385, 712), "Projection fictive du pack 1 : gain de 52 kWh/m²/an.\nValeurs illustratives, non issues d'un calcul 3CL validé.\nLes performances et coûts doivent être confirmés par une étude.", 8)


def technical(page):
    e = Editor(page)
    e.field((41, 140, 552, 166), "Rapport de démonstration. Diagnostiqueur et certification fictifs : Diagnostics Démo Rhône,\nDEMO-CERT-001. Aucune visite ni certification réelle.", 9, True)
    e.field((40, 174, 295, 273), f"Logiciel : générateur de démonstration, non validé\nRéférence DPE : {REFERENCE}\nMéthode représentée : 3CL-DPE 2021, simulation\nDate de visite simulée : 25/08/2026\nInvariant fiscal : non attribué (bien fictif)\nCopropriété : DEMO-RNC-69004-001\nParcelle cadastrale : non attribuée\nSyndicat des copropriétaires Les Tisseurs\n{ADDRESS}", 7.5)
    e.field((304, 174, 552, 273), "Justificatifs synthétiques du scénario :\nRèglement de copropriété et état descriptif de division.\nCarnet d'information du logement.\nAbsence de facture d'isolation des rampants.\n\nAucun relevé physique n'a été réalisé.", 8)
    e.field((82, 383, 550, 453), "Les consommations présentées sont conventionnelles et synthétiques. Elles ne prédisent pas\nles factures réelles, qui dépendent de l'occupation, de la météo et des contrats d'énergie.\nLa surface retenue dans ce DPE fictif est de 64,80 m². Le mesurage Carrez indique 61,50 m².\nL'écart de 3,30 m² doit être rapproché du périmètre et des règles de chaque mesurage.", 9)
    values = ["69 (Rhône)", "Non renseignée", "Appartement, 3e étage, lot 18", "1898", "64,80 m²",
              "Non renseignée", "1", "Non renseigné", "Non renseignée", "16"]
    for i, value in enumerate(values):
        y = 500 + i * 17.02
        e.field((191, y, 269, y + 13), "Scénario fictif", 7, graphics=True)
        e.field((273, y, 555, y + 13), value, 7.5)
    e.finish()


def systems(page):
    e = Editor(page)
    rows = [
        (122.8, "Mur nord : pierre, env. 45 cm, isolation non observée"),
        (145.4, "Mur sud : pierre sur rue, isolation non observée"),
        (168.1, "Orientation nord-sud ; inertie lourde"),
        (190.8, "Autres parois : non documentées"),
        (213.5, "Sur logement chauffé ; déperditions : 0 %"),
        (236.2, "Sous grenier partiellement aménagé ; pertes : 7 %"),
        (258.8, "Double vitrage, cadres bois, pose déclarée en 2019"),
        (281.5, "Persiennes bois sur rue"),
        (304.2, "Caractéristiques thermiques non documentées"),
        (326.9, "Ponts thermiques : 15 % des déperditions"),
        (349.6, "Murs : 31 % des déperditions"),
        (372.2, "Fenêtres et portes : 18 % des déperditions"),
        (394.9, "Ventilation : 29 % des déperditions"),
        (417.6, "Performance globale de l'isolation : insuffisante"),
        (440.3, "Confort d'été : insuffisant, risque sous rampant"),
    ]
    for y, value in rows:
        e.field((188, y - 1, 265, y + 13), "Scénario fictif", 7)
        e.field((269, y - 1, 555, y + 13), value, 7.5)
    e.field((88, 416, 184, 431), "isolation", 7, True)
    e.field((88, 439, 184, 454), "confort d'été", 7, True)
    for y, value in [(522.7, "Conduits naturels ; débits non mesurés"),
                     (548.2, "Radiateurs électriques à effet Joule, 2008 à 2024"),
                     (573.7, "Ballon électrique 150 litres, installé en 2020"),
                     (599.2, "Absente"), (624.7, "Thermostats individuels, programmation partielle"),
                     (650.2, "Aucun équipement individuel")]:
        e.field((200, y - 1, 266, y + 13), "Scénario fictif", 7)
        e.field((269, y - 1, 555, y + 13), value, 7.5)
    e.finish()
    text(page, (89, 624, 195, 639), "régulation", 7, True)
    text(page, (89, 650, 195, 664), "énergies renouvelables", 7, True)


def build_dpe_pdf():
    if hashlib.sha256(TEMPLATE.read_bytes()).hexdigest() != TEMPLATE_SHA256:
        raise ValueError("Official DPE template checksum mismatch; review field coordinates")
    # Graft only reachable page objects into a fresh document. The ministry file
    # contains sparse incremental xrefs and metadata from older specimen versions.
    with fitz.open(TEMPLATE) as source, fitz.open() as doc:
        doc.insert_pdf(source, links=False, annots=False, widgets=False)
        if len(doc) != len(PAGE_TITLES):
            raise ValueError("Unexpected official DPE template page count")
        for page, render in zip(doc, (cover, comfort, consumption, overview,
                                     recommendations, projections, technical, systems)):
            render(page)
            # Same prominent specimen notice, including on the malformed source page 2.
            page.add_redact_annot((0, 0, 595.276, 26), fill=(1, 1, 1), cross_out=False)
            page.apply_redactions(images=2, graphics=1)
            page.draw_rect((0, 7, 595.276, 26), color=None, fill=rgb("ed5b48"))
            text(page, (6, 10, 589, 25), NOTICE, 8.5, True, (1, 1, 1), align=1)
            text(page, (34, 822, 560, 837), f"{REFERENCE}  •  {ADDRESS}  •  {page.number + 1}/8", 6.5, color=rgb("555555"), align=1)
            for link in page.get_links():
                page.delete_link(link)
            for annot in list(page.annots() or []):
                page.delete_annot(annot)
        doc.set_metadata({"title": "Diagnostic de performance énergétique, démonstration Lyon",
                          "author": "Générateur de documents synthétiques",
                          "subject": "Spécimen fictif sur le modèle national, sans valeur contractuelle"})
        doc.del_xml_metadata()
        doc.set_toc([])
        for name in doc.embfile_names():
            doc.embfile_del(name)
        doc.subset_fonts()
        return doc.tobytes(garbage=4, deflate=True, clean=True, no_new_id=True)
