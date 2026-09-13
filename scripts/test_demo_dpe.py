# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf==1.26.7"]
# ///
"""Artifact regression checks: uv run scripts/test_demo_dpe.py."""

import hashlib
import json
import unittest
from pathlib import Path

import pymupdf as fitz

from demo_dpe import ELECTRICITY_PRIMARY_FACTOR, NOTICE, SURFACE, USES, build_dpe_pdf


class DemoDpeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = build_dpe_pdf()
        cls.pdf = fitz.open(stream=cls.content, filetype="pdf")
        cls.pages = [page.get_text() for page in cls.pdf]

    @classmethod
    def tearDownClass(cls):
        cls.pdf.close()

    def test_national_sections_and_searchable_scenario(self):
        self.assertEqual(len(self.pdf), 8)
        for index, title in enumerate((
            "Performance énergétique et climatique", "Schéma des déperditions de chaleur",
            "Montants et consommations annuels", "Vue d’ensemble du logement",
            "Recommandations d’amélioration", "Évolution de la performance après travaux",
            "Fiche technique du logement", "Fiche technique du logement",
        )):
            with self.subTest(page=index + 1):
                self.assertIn(title, self.pages[index])
                self.assertIn(NOTICE, self.pages[index])
                self.assertIn("DEMO-DPE-LYON-001", self.pages[index])
        for field in ("Classe énergie : E", "Classe climat : B", "302", "9 kg CO2/m²/an",
                      "64,80 m²", "1 880 €", "2 650 €", "25/08/2026", "24/08/2036"):
            self.assertIn(field, self.pages[0])
        self.assertIn("61,50 m²", self.pages[6])
        self.assertIn("Radiateurs électriques à effet Joule", self.pages[7])

    def test_specimen_data_and_interactive_objects_are_removed(self):
        all_text = "\n".join(self.pages) + str(self.pdf.metadata)
        for obsolete in ("Roubaix", "Dupont", "Pierre Martin", "PM Diagnostics", "CERTIF 311",
                         "2D20210532", "1234567890", "TC6670042", "000AN0055", "FR410230",
                         "03 88 22", "12/07/2021", "31/08/2035", "<photo", "<url_",
                         "www.faire.gouv.fr", "271", "3 276", "17 129", "12 789",
                         "Chaudière fioul classique", "ROUX", "MOURICHON"):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, all_text)
        self.assertEqual(self.pdf.embfile_count(), 0)
        self.assertEqual(self.pdf.get_xml_metadata(), "")
        self.assertEqual(self.pdf.metadata["creationDate"], "")
        for page in self.pdf:
            self.assertFalse(page.get_links())
            self.assertFalse(list(page.annots() or []))
            self.assertFalse(list(page.widgets() or []))

    def test_consumption_totals_match_cover_and_august_2026_factor(self):
        final = sum(row[0] for row in USES)
        primary = round(final * ELECTRICITY_PRIMARY_FACTOR)
        self.assertEqual(final, 10300)
        self.assertEqual(primary, 19570)
        self.assertEqual(round(primary / SURFACE), 302)
        self.assertEqual(round(final / SURFACE), 159)
        self.assertEqual(sum(row[1] for row in USES), 1880)
        self.assertEqual(sum(row[2] for row in USES), 2650)
        self.assertEqual(sum(row[3] for row in USES), 100)
        for field in ("19 570 kWh", "10 300 kWh é.f.", "1 880 € à 2 650 €"):
            self.assertIn(field, self.pages[2])

    def test_reproducible_output_and_committed_manifest(self):
        self.assertEqual(self.content, build_dpe_pdf())
        directory = Path(__file__).resolve().parents[1] / "docs" / "demo-dossier-lyon"
        manifest = json.loads((directory / "manifest.json").read_text())
        for item in manifest["documents"]:
            content = (directory / item["filename"]).read_bytes()
            with self.subTest(document=item["filename"]), fitz.open(stream=content) as pdf:
                self.assertEqual(item["page_count"], len(pdf))
                self.assertEqual(item["size_bytes"], len(content))
                self.assertEqual(item["sha256"], hashlib.sha256(content).hexdigest())
                if item["logical_id"] == "dpe":
                    self.assertEqual(content, self.content)


if __name__ == "__main__":
    unittest.main()
