import re
from datetime import date
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://chocoladefabriekgouda.nl/"
AGENDA_URL = urljoin(BASE_URL, "agenda")
SOURCE = "Chocoladefabriek Gouda"
MONTHS = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "augustus": 8,
    "september": 9, "oktober": 10, "november": 11, "december": 12,
}
DATE_RE = re.compile(
    r"(?:(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\s+)?"
    r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})",
    re.IGNORECASE,
)


def _get_page(session, url, counts):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    counts["pages_scanned"] += 1
    return response.url, BeautifulSoup(response.content, "html.parser")


def _agenda_urls(soup, page_url):
    for link in soup.select("a[href]"):
        url = urljoin(page_url, link["href"])
        parts = urlsplit(url)
        if parts.netloc == urlsplit(BASE_URL).netloc and re.fullmatch(r"/agenda/[^/]+", parts.path):
            yield url


def _event_date(heading):
    label = heading.find_previous_sibling("p")
    if label is None:
        return None
    match = DATE_RE.search(label.get_text(" ", strip=True))
    if match is None:
        return None
    try:
        event_date = date(int(match.group(3)), MONTHS[match.group(2).lower()], int(match.group(1)))
    except ValueError:
        return None
    return match.group(0).lower(), event_date


def _location(detail):
    heading = detail.find("h1")
    header = heading.find_parent("header") if heading else None
    content = header.find_next_sibling("div") if header else None
    if content is None:
        return ""
    description = content.get_text(" ", strip=True)
    location_icon = content.select_one("i.fa-location")
    location_label = location_icon.parent.get_text(" ", strip=True) if location_icon else ""

    if "niet in de chocoladefabriek" in location_label.casefold():
        # De detailtekst noemt het echte adres van deze activiteit buiten het gebouw.
        match = re.search(
            r"\b(Ontmoetingscentrum Van Noord),\s*(Lekkenburg\s+\d+)\s+in\s+Gouda",
            description,
            re.IGNORECASE,
        )
        return f"{match.group(1)}, {match.group(2)}, Gouda" if match else ""

    if location_label.casefold() == "chocoladefabriek":
        return SOURCE
    if location_label.casefold() == "tweede verdieping" and "chocoladefabriek" in description.casefold():
        return f"Tweede verdieping, {SOURCE}"
    if "techniekwerkplaats" in description.casefold() and "in de chocoladefabriek" in description.casefold():
        return f"Techniekwerkplaats, {SOURCE}"
    return ""


def fetch_events(stats=None):
    counts = {
        "pages_scanned": 0,
        "raw_candidates": 0,
        "recurring_occurrences_expanded": 0,
        "source_level_duplicates": 0,
        "excluded_no_location": 0,
    }
    events = []
    seen_urls = set()
    seen_events = set()
    seen_title_dates = {}

    with requests.Session() as session:
        detail_urls = []
        for page in (BASE_URL, AGENDA_URL):
            page_url, soup = _get_page(session, page, counts)
            urls = list(_agenda_urls(soup, page_url))
            if not urls:
                raise ValueError(f"Geen Chocoladefabriek-agendakaarten gevonden: {page_url}")
            for url in urls:
                counts["raw_candidates"] += 1
                if url in seen_urls:
                    counts["source_level_duplicates"] += 1
                    continue
                seen_urls.add(url)
                detail_urls.append(url)

        for url in detail_urls:
            detail_url, detail = _get_page(session, url, counts)
            heading = detail.find("h1")
            if heading is None:
                raise ValueError(f"Chocoladefabriek-item mist titel: {detail_url}")
            parsed_date = _event_date(heading)
            if parsed_date is None:
                raise ValueError(f"Chocoladefabriek-item mist expliciete datum: {detail_url}")
            date_text, event_date = parsed_date
            if event_date <= date.today():
                continue
            location = _location(detail)
            if not location:
                counts["excluded_no_location"] += 1
                continue
            title = heading.get_text(" ", strip=True)
            key = (title.casefold(), event_date, location.casefold(), "Gouda")
            if key in seen_events:
                counts["source_level_duplicates"] += 1
                continue
            seen_events.add(key)
            title_key = title.casefold()
            if title_key in seen_title_dates and event_date not in seen_title_dates[title_key]:
                counts["recurring_occurrences_expanded"] += 1
            seen_title_dates.setdefault(title_key, set()).add(event_date)
            events.append({
                "title": title,
                "date_text": date_text,
                "location": location,
                "city": "Gouda",
                "source": SOURCE,
                "source_url": detail_url,
            })

    counts["final_event_occurrences"] = len(events)
    if stats is not None:
        stats.update(counts)
    return events
