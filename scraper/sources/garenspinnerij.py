from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SOURCE_URL = "https://cultuurhuisgarenspinnerij.nl/kalender/"
SOURCE_NAME = "Cultuurhuis Garenspinnerij"


def fetch_events():
    events = []
    seen_events = set()
    visited_pages = set()
    page_url = SOURCE_URL

    while page_url and page_url not in visited_pages:
        visited_pages.add(page_url)
        response = requests.get(page_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        agenda = soup.select_one("main .w-grid.us_post_list")
        if agenda is None:
            raise ValueError("De agenda van Cultuurhuis Garenspinnerij is niet gevonden.")

        # Alleen de agendalijst, niet de carrousel, het archief of de voettekst.
        for card in agenda.select("article.type-agenda:not(.filter-archief)"):
            title_element = card.select_one(".post_title")
            start_element = card.select_one(".begindatum")
            if title_element is None or start_element is None:
                continue

            title = title_element.get_text(" ", strip=True)
            date_text = start_element.get_text(" ", strip=True)
            if not title or not date_text:
                continue

            end_element = card.select_one(".acf-vervaldatum")
            if end_element is not None:
                end_text = end_element.get_text(" ", strip=True).lstrip("–—- ")
                if end_text and end_text != date_text:
                    date_text += " – " + end_text

            link = title_element.select_one("a[href]")
            location_element = card.select_one(".post_custom_field.locatie")
            description_element = card.select_one(".samenvatting .w-post-elm-value, .samenvatting")
            location = location_element.get_text(" ", strip=True) if location_element else ""
            event = {
                "title": title,
                "date_text": date_text,
                "time_text": None,
                "description": (
                    description_element.get_text(" ", strip=True) if description_element else None
                ),
                "location": location or SOURCE_NAME,
                "city": "Gouda",
                "source": SOURCE_NAME,
                "source_url": urljoin(page_url, link["href"]) if link else SOURCE_URL,
            }
            key = tuple(event.values())
            if key not in seen_events:
                seen_events.add(key)
                events.append(event)

        next_page = agenda.select_one("a.next.page-numbers[href]")
        page_url = urljoin(page_url, next_page["href"]) if next_page else None

    return events
