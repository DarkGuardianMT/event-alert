import json
from datetime import date
from urllib.parse import urljoin, urldefrag

import requests
from bs4 import BeautifulSoup


SOURCE_URL = "https://uitgouda.com/events/"
MONTHS = (
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
)


def _event_nodes(value):
    if isinstance(value, dict):
        types = value.get("@type", [])
        if types == "Event" or isinstance(types, list) and "Event" in types:
            yield value
        for child in value.values():
            yield from _event_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _event_nodes(child)


def _structured_events(soup):
    events = {}
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.get_text())
        except json.JSONDecodeError:
            continue
        for event in _event_nodes(data):
            url = event.get("url")
            if isinstance(url, str):
                key = urldefrag(urljoin(SOURCE_URL, url))[0].rstrip("/")
                if key in events and any(
                    events[key].get(field) != event.get(field)
                    for field in ("startDate", "endDate")
                ):
                    raise ValueError(f"Tegenstrijdige UitGouda-datums: {url}")
                events[key] = event
    return events


def _date_text(value):
    # Behoud de lokale kalenderdatum uit de bron, zonder tijdzoneconversie.
    parsed = date.fromisoformat(value.split("T", 1)[0])
    return parsed, f"{parsed.day} {MONTHS[parsed.month - 1]} {parsed.year}"


def fetch_events(stats=None):
    counts = {"raw_cards": 0, "listing_dates": 0, "detail_dates": 0, "duplicates": 0}
    events = []
    seen = set()
    details = {}

    with requests.Session() as session:
        response = session.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        listing = _structured_events(soup)
        cards = soup.select("article.event-card")
        if not cards:
            raise ValueError("Geen UitGouda-evenementkaarten gevonden.")
        counts["raw_cards"] = len(cards)

        for card in cards:
            title_element = card.select_one("h3")
            link = card.select_one("a.event-card-link[href]")
            if title_element is None or link is None:
                raise ValueError("UitGouda-evenement mist een titel of detail-URL.")
            url = urljoin(SOURCE_URL, link["href"])
            key = urldefrag(url)[0].rstrip("/")
            listed = listing.get(key, {})
            event_data = listed
            if listed.get("startDate") and listed.get("endDate"):
                counts["listing_dates"] += 1
            else:
                if key not in details:
                    response = session.get(url, timeout=30)
                    response.raise_for_status()
                    detail = BeautifulSoup(response.content, "html.parser")
                    details[key] = _structured_events(detail).get(key, {})
                event_data = details[key]
                counts["detail_dates"] += 1

            if not event_data.get("startDate") or not event_data.get("endDate"):
                raise ValueError(f"Exacte UitGouda-datums ontbreken: {url}")
            start, start_text = _date_text(event_data["startDate"])
            end, end_text = _date_text(event_data["endDate"])
            if end < start or (
                listed.get("startDate") and _date_text(listed["startDate"])[0] != start
            ):
                raise ValueError(f"Tegenstrijdige UitGouda-datums: {url}")

            location = event_data.get("location") or {}
            location = location.get("name", "") if isinstance(location, dict) else ""
            event = {
                "title": title_element.get_text(" ", strip=True),
                "date_text": start_text if start == end else f"{start_text} – {end_text}",
                "location": location or "",
                "city": "Gouda",
                "source": "UitGouda",
                "source_url": url,
            }
            fingerprint = tuple(event.values())
            if fingerprint in seen:
                counts["duplicates"] += 1
                continue
            seen.add(fingerprint)
            events.append(event)

    if stats is not None:
        stats.update(counts)
    return events
