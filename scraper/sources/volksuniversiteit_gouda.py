import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from sources.http import SourceSession


SOURCE_URL = "https://www.volksuniversiteitgouda.nl/agenda"
MONTHS = (
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
)


def _date_text(value):
    event_date = datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    return f"{event_date.day} {MONTHS[event_date.month - 1]} {event_date.year}"


def fetch_events(stats=None):
    counts = {"agenda_entries": 0, "included": 0, "excluded": 0, "duplicates": 0}
    events = []
    seen_events = set()
    visited_pages = set()
    page_url = SOURCE_URL

    with SourceSession(SOURCE_URL) as session:
        while page_url and page_url not in visited_pages:
            visited_pages.add(page_url)
            response = session.get(page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            cards = soup.select("div.commerce-product-variation.agenda.full-agenda")
            if not cards:
                raise ValueError("Geen Volksuniversiteit-agenda-items gevonden.")

            for card in cards:
                counts["agenda_entries"] += 1
                title_link = card.select_one("h3.title a[href]")
                date_element = card.select_one("time.datetime[datetime]")
                if title_link is None or date_element is None:
                    raise ValueError("Volksuniversiteit-item mist een titel, URL of datum.")

                detail_url = urljoin(page_url, title_link["href"])
                detail_response = session.get(detail_url, timeout=30)
                detail_response.raise_for_status()
                detail = BeautifulSoup(detail_response.content, "html.parser")
                sessions = [
                    item for item in detail.select(".course-info-item.calendar .vu_session_info")
                    if re.match(r"\s*\d+\s*:", item.get_text(" ", strip=True))
                ]
                if len(sessions) != 1:
                    counts["excluded"] += 1
                    continue

                location_element = sessions[0].select_one(".location")
                location = location_element.get_text(" ", strip=True).lstrip("–—- ") if location_element else ""
                session_text = sessions[0].get_text(" ", strip=True)
                time_match = re.search(r"-\s*([01]?\d|2[0-3])[:.]([0-5]\d)\b", session_text)
                description_element = detail.select_one(".region-content .field--name-body")
                event = {
                    "title": title_link.get_text(" ", strip=True),
                    "date_text": _date_text(date_element["datetime"]),
                    "time_text": (
                        f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
                        if time_match else None
                    ),
                    "description": (
                        description_element.get_text(" ", strip=True)
                        if description_element else None
                    ),
                    "location": location,
                    "city": "Gouda",
                    "source": "Volksuniversiteit Gouda",
                    "source_url": detail_url,
                }
                fingerprint = tuple(event.values())
                if fingerprint in seen_events:
                    counts["duplicates"] += 1
                    continue
                seen_events.add(fingerprint)
                events.append(event)
                counts["included"] += 1

            next_page = soup.select_one('nav.pager a[rel="next"][href]')
            page_url = urljoin(page_url, next_page["href"]) if next_page else None

    if stats is not None:
        stats.update(counts)
    return events
