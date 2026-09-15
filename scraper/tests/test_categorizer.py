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
        self.assertEqual(classify({"title": "Onbekende activiteit"}), {"other"})

    def test_input_is_not_changed(self):
        event = {"title": "  Wijkfeest\tGouda Noord  ", "source": "Gemeente Gouda"}
        original = event.copy()
        self.assertEqual(classify(event), {"community"})
        self.assertEqual(event, original)


if __name__ == "__main__":
    unittest.main()
