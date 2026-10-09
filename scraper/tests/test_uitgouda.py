import json
import unittest
from unittest.mock import patch

from sources import uitgouda


class UitGoudaTests(unittest.TestCase):
    def test_event_without_confirmed_city_is_excluded(self):
        events = [
            {
                "@type": "Event",
                "url": "https://uitgouda.com/event/known/",
                "startDate": "2026-10-01T12:00:00",
                "endDate": "2026-10-01T13:00:00",
                "location": {"name": "Bibliotheek", "address": {"addressLocality": "Gouda"}},
            },
            {
                "@type": "Event",
                "url": "https://uitgouda.com/event/unknown/",
                "startDate": "2026-10-02T12:00:00",
                "endDate": "2026-10-02T13:00:00",
                "location": {"name": "Onbekende locatie"},
            },
        ]
        cards = (
            '<article class="event-card"><h3>Bekend</h3>'
            '<a class="event-card-link" href="/event/known/"></a></article>'
            '<article class="event-card"><h3>Onbekend</h3>'
            '<a class="event-card-link" href="/event/unknown/"></a></article>'
        )
        html = f'<script type="application/ld+json">{json.dumps(events)}</script>{cards}'

        with patch.object(uitgouda, "SourceSession") as session:
            session.return_value.__enter__.return_value.get.return_value.content = html.encode()
            stats = {}
            result = uitgouda.fetch_events(stats)

        self.assertEqual([event["title"] for event in result], ["Bekend"])
        self.assertEqual(result[0]["city"], "Gouda")
        self.assertEqual(stats["raw_cards"], 2)
        self.assertEqual(stats["excluded_missing_city"], 1)


if __name__ == "__main__":
    unittest.main()
