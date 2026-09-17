import unittest

from sources.sportpunt_gouda import _single_time_text


class SportpuntMetadataTests(unittest.TestCase):
    def test_explicit_ranges_are_kept(self):
        self.assertEqual(_single_time_text("Tijd: 16.30-17.30 uur"), "16:30 - 17:30")
        self.assertEqual(
            _single_time_text("Tijd: vrije inloop tussen 11.30 en 12.30 uur"),
            "11:30 - 12:30",
        )

    def test_separate_schedule_times_are_not_turned_into_a_range(self):
        self.assertIsNone(_single_time_text("Tijd: inloop 19.00 uur, start 19.15 uur"))

    def test_single_explicit_time_is_kept(self):
        self.assertEqual(_single_time_text("Tijd: 14:00 uur"), "14:00")


if __name__ == "__main__":
    unittest.main()
