import json
import re
from datetime import date, datetime
from urllib.parse import urljoin, urldefrag

import requests
from bs4 import BeautifulSoup


SOURCE_URL = "https://uitgouda.com/events/"
MONTHS = (
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
)
KNOWN_CITIES = ("Gouda", "Waddinxveen", "Bodegraven", "Haastrecht", "Reeuwijk")
CLOCK_RE = re.compile(r"(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)(?!\d)")


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


def _card_start_time(card):
    metadata = card.select_one(".event-card-meta")
    match = CLOCK_RE.search(metadata.get_text(" ", strip=True)) if metadata else None
    if match is None:
        return None
    return f"{int(match.group(1)):02d}:{match.group(2)}"


def _time_text(event_data, visible_start):
    if not visible_start or not event_data.get("startDate"):
        return None
    try:
        start = datetime.fromisoformat(event_data["startDate"].replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if start.strftime("%H:%M") != visible_start:
        return None

    value = visible_start
    try:
        end = datetime.fromisoformat(event_data["endDate"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return value
    if end.date() == start.date() and end > start and end.strftime("%H:%M:%S") != "23:59:59":
        value += " - " + end.strftime("%H:%M")
    return value


def _city(event_data):
    location = event_data.get("location") or {}
    if not isinstance(location, dict):
        return ""

    address = location.get("address") or {}
    address_text = " ".join(
        str(value) for key, value in address.items()
        if key != "addressLocality" and isinstance(value, str)
    ) if isinstance(address, dict) else str(address)
    location_text = f"{location.get('name', '')} {address_text}"

    # Een expliciete plaats in het locatieadres gaat voor foutieve bronmetadata.
    for city in KNOWN_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", location_text, re.IGNORECASE):
            return city

    locality = address.get("addressLocality", "") if isinstance(address, dict) else ""
    return locality.strip() if isinstance(locality, str) else ""


def fetch_events(stats=None):
    counts = {
        "raw_cards": 0, "listing_dates": 0, "detail_dates": 0,
        "duplicates": 0, "excluded_missing_city": 0,
    }
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
                "time_text": _time_text(event_data, _card_start_time(card)),
                "description": None,
                "location": location or "",
                "city": _city(event_data),
                "source": "UitGouda",
                "source_url": url,
            }
            if not event["city"]:
                # Zonder bevestigde plaats kan dit evenement niet veilig worden opgeslagen.
                counts["excluded_missing_city"] += 1
                continue
            fingerprint = tuple(event.values())
            if fingerprint in seen:
                counts["duplicates"] += 1
                continue
            seen.add(fingerprint)
            events.append(event)

    if stats is not None:
        stats.update(counts)
    return events
