import unittest

from normalizer import normalize_description, normalize_event, normalize_time


class TimeNormalizerTests(unittest.TestCase):
    def test_supported_time_formats(self):
        cases = {
            "19:30": {"start_time": "19:30:00", "end_time": None},
            "09.00": {"start_time": "09:00:00", "end_time": None},
            "19:30 uur": {"start_time": "19:30:00", "end_time": None},
            "19.30 uur": {"start_time": "19:30:00", "end_time": None},
            "19:30 - 21:00": {"start_time": "19:30:00", "end_time": "21:00:00"},
            "19.30–21.00": {"start_time": "19:30:00", "end_time": "21:00:00"},
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(normalize_time(value), expected)

    def test_missing_or_vague_time_stays_empty(self):
        for value in (None, "", "iedere woensdag", "vanaf de avond"):
            with self.subTest(value=value):
                self.assertEqual(normalize_time(value), {"start_time": None, "end_time": None})

    def test_date_only_event_gets_nullable_metadata(self):
        event = normalize_event({"title": "Datum zonder tijd", "date_text": "24 september 2026"})
        self.assertEqual(event["start_date"], "2026-09-24")
        self.assertIsNone(event["start_time"])
        self.assertIsNone(event["end_time"])
        self.assertIsNone(event["description"])

    def test_description_whitespace_and_limit(self):
        self.assertEqual(normalize_description("  Een\n korte   tekst. "), "Een korte tekst.")
        shortened = normalize_description("woord " * 500, max_length=40)
        self.assertLessEqual(len(shortened), 41)
        self.assertTrue(shortened.endswith("…"))


if __name__ == "__main__":
    unittest.main()
