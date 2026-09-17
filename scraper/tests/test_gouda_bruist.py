import unittest
from collections import defaultdict
from datetime import date
from unittest.mock import patch

from bs4 import BeautifulSoup

from collector import collect_source_results
from sources import gouda_bruist


def card_html(activity_id, title="Testactiviteit", day=18, month="sep",
              clock="10:00-12:00", location="Testlocatie"):
    return f"""
        <a class="go_card-activity" href="/engine?service=x&amp;id={activity_id}">
          <div class="go_date-day-wrapper">{day}</div>
          <div class="go_date-month-wrapper">{month}</div>
          <div class="go_date-time-wrapper">{clock}</div>
          <h3 class="go_card-title-wrapper">{title}</h3>
          <div class="go_card-meta-line"><span>{location}</span></div>
        </a>
    """


def detail_html(date_text="vr 18 sep 2026, 10:00 - 12:00 uur", location_id="7",
                event_type="Bijeenkomst", description="Volledige beschrijving."):
    location = (
        f'<a class="go_card-location" href="/engine?service=location&amp;id={location_id}">'
        "Locatie</a>" if location_id else ""
    )
    return f"""
      <article class="go_wall-card-content">
        <header>
          <div class="go_card-meta-line"><i title="Datum"></i><span>{date_text}</span></div>
          <div class="go_card-meta-line"><i title="Locatie"></i><span>Testlocatie</span></div>
        </header>
        <section class="go_wall-card-main-module-wrapper">
          <div class="go_wall-card-module"><p>{description}</p></div>
        </section>
        <div class="go_property"><dt>Type</dt><dd>{event_type}</dd></div>
      </article>
      {location}
    """


def location_html(city="Gouda", venue="Testlocatie"):
    return f"""
      <article class="go_wall-card-content"><header>
        <h1>{venue}</h1><div class="go_adress-wrapper">Teststraat 1, {city}</div>
      </header></article>
    """


class FakeResponse:
    def __init__(self, html, url="https://goudabruist.nl/test", status=200):
        self.content = html.encode("utf-8")
        self.url = url
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, get_responses=(), post_responses=()):
        self.get_responses = list(get_responses)
        self.post_responses = list(post_responses)
        self.get_calls = []
        self.post_calls = []

    def get(self, url, **kwargs):
        self.get_calls.append(url)
        return self.get_responses.pop(0)

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        return self.post_responses.pop(0)


def parsed_card(activity_id="1", title="Testactiviteit", day=18, month=9,
                clock="10:00-12:00", location="Testlocatie"):
    return {
        "activity_id": activity_id,
        "engine_url": f"https://goudabruist.nl/engine?id={activity_id}",
        "title": title,
        "day": day,
        "month": month,
        "time_text": clock,
        "location": location,
    }


def parsed_detail(start=date(2026, 9, 1), end=date(2026, 9, 30),
                  location_id="7", event_type="Bijeenkomst"):
    return {
        "url": "https://goudabruist.nl/activiteit/1/testactiviteit",
        "start_date": start,
        "end_date": end,
        "description": "Volledige beschrijving.",
        "detail_location": "Testlocatie",
        "location_id": location_id,
        "location_url": f"https://goudabruist.nl/engine?id={location_id}",
        "properties": {"type": event_type},
    }


class GoudaBruistTests(unittest.TestCase):
    def test_listing_card_parsing(self):
        soup = BeautifulSoup(card_html("42"), "html.parser")
        card = gouda_bruist._parse_card(soup.select_one(".go_card-activity"))
        self.assertEqual(card["activity_id"], "42")
        self.assertEqual((card["day"], card["month"]), (18, 9))
        self.assertEqual(card["location"], "Testlocatie")

    def test_pagination_uses_post_and_stops_on_short_page(self):
        first = card_html("1") + card_html("2", day=19)
        second = card_html("3", day=20)
        session = FakeSession(
            [FakeResponse(first, gouda_bruist.LISTING_URL)],
            [FakeResponse(second, gouda_bruist.LISTING_URL)],
        )
        counts = defaultdict(int)
        with patch.object(gouda_bruist, "PAGE_SIZE", 2):
            cards = gouda_bruist._listing_cards(session, counts)
        self.assertEqual(len(cards), 3)
        self.assertEqual(len(session.post_calls), 1)
        self.assertIn("from=2&increment=2", session.post_calls[0][0])
        self.assertEqual(session.post_calls[0][1]["headers"]["X-Requested-With"], "XMLHttpRequest")

    def test_detail_uses_canonical_response_url(self):
        canonical = "https://goudabruist.nl/activiteit/1/testactiviteit"
        session = FakeSession([FakeResponse(detail_html(), canonical)])
        detail = gouda_bruist._fetch_detail(session, parsed_card(), defaultdict(int))
        self.assertEqual(detail["url"], canonical)
        self.assertEqual(detail["description"], "Volledige beschrijving.")

    def test_detail_without_explicit_bounds_is_deferred(self):
        html = detail_html("Op maandag en woensdag, 10:00 - 12:00 uur")
        session = FakeSession([FakeResponse(html)])
        counts = defaultdict(int)
        detail = gouda_bruist._fetch_detail(session, parsed_card(), counts)
        self.assertIsNone(detail["start_date"])
        self.assertEqual(counts["details_without_date_bounds"], 1)

    def test_explicit_year_mapping(self):
        result = gouda_bruist._resolve_occurrence_date(
            7, 1, date(2026, 12, 1), date(2027, 2, 1)
        )
        self.assertEqual(result, date(2027, 1, 7))

    def test_ambiguous_year_is_rejected(self):
        result = gouda_bruist._resolve_occurrence_date(
            7, 1, date(2026, 1, 1), date(2027, 12, 31)
        )
        self.assertIsNone(result)

    def test_start_and_end_time(self):
        counts = defaultdict(int)
        self.assertEqual(gouda_bruist._time_text("9:05-12:30", counts), "09:05 - 12:30")
        self.assertEqual(counts["suspicious_time_ranges"], 0)

    def test_start_only_time(self):
        self.assertEqual(gouda_bruist._time_text("19:15", defaultdict(int)), "19:15")

    def test_city_gouda_is_case_insensitive(self):
        status = gouda_bruist._location_status(
            [parsed_card()], parsed_detail(), {"city": "GOUDA", "venue": "Testlocatie"}
        )
        self.assertEqual(status, "gouda")

    def test_unresolved_city_is_excluded(self):
        card = parsed_card(location="Buurtcentrum")
        counts = defaultdict(int)
        events = gouda_bruist._build_events(
            [card], {"1": parsed_detail()}, {}, counts
        )
        self.assertEqual(events, [])
        self.assertEqual(counts["excluded_unresolved_city"], 1)

    def test_non_gouda_city_is_excluded(self):
        counts = defaultdict(int)
        events = gouda_bruist._build_events(
            [parsed_card()], {"1": parsed_detail()},
            {"7": {"city": "Rotterdam"}}, counts,
        )
        self.assertEqual(events, [])
        self.assertEqual(counts["excluded_outside_gouda"], 1)

    def test_online_event_is_excluded(self):
        counts = defaultdict(int)
        events = gouda_bruist._build_events(
            [parsed_card(location="Online")], {"1": parsed_detail()}, {}, counts
        )
        self.assertEqual(events, [])
        self.assertEqual(counts["excluded_online"], 1)

    def test_location_pages_are_cached_by_id(self):
        session = FakeSession([FakeResponse(location_html(), "https://goudabruist.nl/locatie/7/test")])
        details = {
            "1": parsed_detail(location_id="7"),
            "2": parsed_detail(location_id="7"),
        }
        locations = gouda_bruist._locations_by_id(session, details, defaultdict(int))
        self.assertEqual(tuple(locations), ("7",))
        self.assertEqual(len(session.get_calls), 1)

    def test_detail_pages_are_cached_by_activity_id(self):
        canonical = "https://goudabruist.nl/activiteit/1/test"
        session = FakeSession([FakeResponse(detail_html(), canonical)])
        cards = [parsed_card(), parsed_card(day=19)]
        details = gouda_bruist._details_by_activity(session, cards, defaultdict(int))
        self.assertEqual(tuple(details), ("1",))
        self.assertEqual(len(session.get_calls), 1)

    def test_discrete_recurrence_expands_explicit_cards(self):
        cards = [parsed_card(day=18), parsed_card(day=25)]
        counts = defaultdict(int)
        events = gouda_bruist._build_events(
            cards, {"1": parsed_detail()}, {"7": {"city": "Gouda"}}, counts
        )
        self.assertEqual([event["date_text"] for event in events], [
            "18 september 2026", "25 september 2026",
        ])
        self.assertEqual(counts["discrete_recurring_occurrences"], 2)

    def test_continuous_exhibition_is_collapsed(self):
        cards = [parsed_card(day=18), parsed_card(day=19)]
        detail = parsed_detail(event_type="Tentoonstelling")
        counts = defaultdict(int)
        events = gouda_bruist._build_events(
            cards, {"1": detail}, {"7": {"city": "Gouda"}}, counts
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["date_text"], "1 september 2026 - 30 september 2026")
        self.assertEqual(counts["collapsed_continuous_ranges"], 1)

    def test_source_level_duplicate_uses_production_identity(self):
        cards = [parsed_card("1"), parsed_card("2")]
        details = {"1": parsed_detail(), "2": parsed_detail()}
        counts = defaultdict(int)
        events = gouda_bruist._build_events(
            cards, details, {"7": {"city": "Gouda"}}, counts
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(counts["source_level_duplicates"], 1)

    def test_suspicious_time_keeps_only_start(self):
        counts = defaultdict(int)
        self.assertEqual(gouda_bruist._time_text("19:00-0:00", counts), "19:00")
        self.assertEqual(counts["suspicious_time_ranges"], 1)

    def test_incomplete_source_is_rejected_before_sync(self):
        counts = defaultdict(int, {
            "raw_listing_cards": 40,
            "distinct_activity_ids": 40,
            "final_event_occurrences": 40,
        })
        with self.assertRaisesRegex(ValueError, "verdacht weinig activiteitenkaarten"):
            gouda_bruist._ensure_healthy(counts)

    def test_failed_source_remains_separate_from_successful_source(self):
        def failed():
            raise RuntimeError("gedeeltelijke bronrespons")

        def successful():
            return [{
                "title": "Veilig evenement",
                "date_text": "18 september 2026",
                "source": "Andere bron",
            }]

        successful_results, failed_results = collect_source_results((
            ("Gouda Bruist", failed),
            ("Andere bron", successful),
        ))
        self.assertEqual(tuple(successful_results), ("Andere bron",))
        self.assertEqual(tuple(failed_results), ("Gouda Bruist",))


if __name__ == "__main__":
    unittest.main()
