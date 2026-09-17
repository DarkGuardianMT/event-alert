import unittest

from categorizer import classify


class CategorizerTests(unittest.TestCase):
    def test_requested_examples(self):
        examples = (
            ("Buurtsport 12+ voor meiden", "SPORT•GOUDA", "", {"sport", "community", "kids_family"}),
            ("Kinderboekencafé", "Chocoladefabriek Gouda", "", {"kids_family", "culture"}),
            ("Historische Leesclub", "UitGouda", "", {"culture", "community"}),
            ("Expositie: Kunstgeluk", "Cultuurhuis Garenspinnerij", "", {"exhibition", "culture"}),
            ("Open Monumentendag", "Cultuurhuis Garenspinnerij", "", {"culture"}),
            ("Taalcafé", "UitGouda", "", {"community"}),
            ("Yoga tussen de schuttersstukken", "UitGouda", "Museum Gouda", {"sport"}),
            ("Snijtechnieken", "Volksuniversiteit Gouda", "", {"workshop"}),
            ("Lezing · Leendert van der Valk", "UitGouda", "Chocoladefabriek Gouda", {"lecture"}),
            ("Wijkfeest Gouda Noord", "Gemeente Gouda", "", {"community"}),
        )
        for title, source, location, expected in examples:
            with self.subTest(title=title):
                self.assertEqual(classify({"title": title, "source": source, "location": location}), expected)

    def test_false_positives_and_fallback(self):
        self.assertEqual(classify({"title": "Supermarktopening"}), {"other"})
        self.assertEqual(classify({"title": "Cursus verkeersregels", "source": "Volksuniversiteit Gouda"}), {"other"})
        self.assertEqual(classify({"title": "Yoga", "location": "Museum Gouda"}), {"sport"})
        self.assertEqual(classify({"title": "Theater Concordia • Haastrecht"}), {"other"})
        self.assertEqual(classify({"title": "Bandenwissel"}), {"other"})
        self.assertEqual(classify({"title": "Plankenkoorts"}), {"other"})
        self.assertEqual(classify({"title": "Banenmarkt"}), {"other"})
        self.assertEqual(classify({"title": "Zomerfestival"}), {"other"})
        self.assertEqual(classify({"title": "Samen sterker"}), {"other"})
        self.assertEqual(classify({"title": "Truckrun"}), {"other"})
        self.assertEqual(classify({"title": "Open Dag 2026"}), {"other"})
        self.assertEqual(
            classify({
                "title": "Henri Matisse",
                "source": "UitGouda",
                "source_url": "https://www.volksuniversiteitgouda.nl/kunst-cultuur/henri-matisse",
            }),
            {"other"},
        )
        self.assertEqual(
            classify({
                "title": "Opfriscursus verkeersregels",
                "source": "Volksuniversiteit Gouda",
                "source_url": "https://www.volksuniversiteitgouda.nl/lifestyle-mens-maatschappij/verkeer",
            }),
            {"other"},
        )
        self.assertEqual(classify({"title": "Onbekende activiteit"}), {"other"})

    def test_quality_audit_rules(self):
        examples = (
            ({"title": "Grunge Unplugged Undercoversessie"}, {"culture"}),
            ({"title": "De Verwondering – gratis voorstelling"}, {"culture"}),
            ({"title": "Energy – Introdans"}, {"culture"}),
            ({"title": "Black Gospel Nights"}, {"culture"}),
            ({"title": "Kerst met de Verenigde Mannenkoren"}, {"culture"}),
            ({"title": "The Music of the Lord of the Rings"}, {"culture"}),
            ({"title": "Thrash Metal Party"}, {"culture"}),
            ({"title": "Hyeena met videoclip opname"}, {"culture"}),
            ({"title": "A Night at the Museum"}, {"culture"}),
            ({"title": "Superdrum"}, {"culture"}),
            ({"title": "Bieb voor de Kleintjes"}, {"kids_family"}),
            ({"title": "Jongerenkoor Loïs"}, {"kids_family", "culture"}),
            ({"title": "Yap & Yarn: Draadkracht"}, {"community"}),
            ({"title": "Gouda bij Kaarslicht"}, {"community", "culture"}),
            ({"title": "Sint-Michielsgilde Koningstoernooi"}, {"sport"}),
            ({
                "title": "Cajun",
                "source": "Volksuniversiteit Gouda",
                "source_url": "https://www.volksuniversiteitgouda.nl/culinair/cajun?v=1",
            }, {"workshop"}),
            ({
                "title": "Henri Matisse",
                "source": "Volksuniversiteit Gouda",
                "source_url": "https://www.volksuniversiteitgouda.nl/kunst-cultuur/henri-matisse?v=1",
            }, {"culture"}),
        )
        for event, expected in examples:
            with self.subTest(title=event["title"]):
                self.assertEqual(classify(event), expected)

    def test_input_is_not_changed(self):
        event = {"title": "  Wijkfeest\tGouda Noord  ", "source": "Gemeente Gouda"}
        original = event.copy()
        self.assertEqual(classify(event), {"community"})
        self.assertEqual(event, original)

    def test_gouda_bruist_quality_rules(self):
        examples = (
            ({"title": "Warme maaltijd zoals thuis"}, {"community"}),
            ({"title": "Open Coffee Gouda"}, {"community"}),
            ({"title": "Ontmoetingscafe in de Chocoladefabriek"}, {"community"}),
            ({"title": "5-daagse Cursus Fotografie"}, {"culture", "workshop"}),
            ({
                "title": "Herfstvakantie activiteit: fotografieworkshop voor ouder en kind",
            }, {"culture", "kids_family", "workshop"}),
            ({"title": "Textielfestijn Draden van Verbeelding"}, {"exhibition"}),
            ({
                "title": "Waarheidsgetrouwe en andere beelden die verbazen",
                "description": "Op zondag wordt de expositie Als je van beelden houdt geopend.",
            }, {"exhibition"}),
        )
        for event, expected in examples:
            with self.subTest(title=event["title"]):
                self.assertEqual(classify(event), expected)

    def test_gouda_bruist_rules_avoid_false_positives(self):
        examples = (
            "Kom helpen bij de appel- en perenpluk",
            "Open dag bij de koffiebranderij",
            "Cursus verkeersregels",
            "Samen eten we gezonder",
        )
        for title in examples:
            with self.subTest(title=title):
                self.assertEqual(classify({"title": title}), {"other"})
        self.assertEqual(
            classify({
                "title": "Henri Matisse",
                "description": "Musea maken tentoonstellingen met werken uit hun collectie.",
            }),
            {"other"},
        )
        self.assertEqual(
            classify({
                "title": "Netwerkbijeenkomst",
                "description": "Er is koffie tijdens de open bijeenkomst.",
            }),
            {"other"},
        )


if __name__ == "__main__":
    unittest.main()
