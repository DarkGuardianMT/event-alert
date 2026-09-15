import re
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.sportpuntgouda.nl"
NEWS_URL = f"{BASE_URL}/nieuws"
GIRLS_URL = f"{BASE_URL}/buurtsport-12-voor-meiden"
SOURCE = "SPORT•GOUDA"
MONTHS = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "augustus": 8,
    "september": 9, "oktober": 10, "november": 11, "december": 12,
}
DATE_RE = re.compile(
    r"(?:(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\s+)?"
    r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")(?:\s+(\d{4}))?",
    re.IGNORECASE,
)
UNRELIABLE_SCHEDULES = {
    "/buurtsport-12-": "Schoolvakanties en feestdagen worden overgeslagen; exacte datums ontbreken.",
    "/buurtsport-12-voor-jongens": "Schoolvakanties en feestdagen worden overgeslagen; exacte datums ontbreken.",
    "/stap-mee_2": "Het vakantierooster wijkt af; exacte datums ontbreken.",
    "/vitaal-55-sport-en-beweeglessen-met-docent": "Het vakantierooster wijkt af; exacte datums ontbreken.",
    "/vitaal-55-sportinstfuif": "Het gepubliceerde rooster is voor 2025-2026.",
    "/sportcampus-gouda": "De sporthal wisselt per periode en exacte datums ontbreken.",
}
ACTIVITY_WORDS = (
    "sport", "beweeg", "bewegen", "vitaal", "valpreventie", "zwem", "spel",
    "buurtsport", "wandelen", "valbus", "instuif", "toernooi", "urban", "skate",
)
NON_PUBLIC_WORDS = ("bijeenkomst", "netwerk", "cursus", "training")
GOUDA_VENUES = ("garenspinnerij", "groenhovenbad", "gymzaal isv", "sporthal de zebra", "sportcentrum de mammoet")


def _page(session, url, counts):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    counts["source_pages_scanned"] += 1
    return BeautifulSoup(response.content, "html.parser")


def _date_from_text(text, published=None):
    match = DATE_RE.search(text)
    if match is None:
        return None
    day, month_name, year_text = match.groups()
    month = MONTHS[month_name.lower()]
    if year_text:
        year = int(year_text)
    elif published and month == published.month and int(day) >= published.day:
        # Een dag later in dezelfde publicatiemaand hoort bij het publicatiejaar.
        year = published.year
    else:
        return None
    try:
        return date(year, month, int(day))
    except ValueError:
        return None


def _date_text(event_date):
    month_name = next(name for name, number in MONTHS.items() if number == event_date.month)
    return f"{event_date.day} {month_name} {event_date.year}"


def _add(events, seen, counts, title, event_date, location, url, kind):
    counts["raw_candidate_activities"] += 1
    if event_date <= date.today() or not title or not location:
        return
    key = (title.casefold(), event_date, "Gouda")
    if key in seen:
        counts["source_level_duplicates"] += 1
        return
    seen.add(key)
    events.append({
        "title": title,
        "date_text": _date_text(event_date),
        "location": location,
        "city": "Gouda",
        "source": SOURCE,
        "source_url": url,
    })
    counts[f"{kind}_included"] += 1


def _girls_occurrences(soup, events, seen, counts):
    main = soup.find("main")
    if main is None or "We gaan sporten op:" not in main.get_text(" ", strip=True):
        raise ValueError("SPORT•GOUDA meidenpagina mist de expliciete datums.")
    location_match = re.search(r"Waar:\s*(.+?Gouda)", main.get_text(" ", strip=True))
    if location_match is None:
        raise ValueError("SPORT•GOUDA meidenpagina mist de locatie.")
    location = location_match.group(1)
    date_paragraphs = [
        p.get_text(" ", strip=True) for p in main.find_all("p")
        if not p.find("p") and (
            "We gaan sporten op:" in p.get_text(" ", strip=True)
            or re.match(r"^20\d{2}\s+\d", p.get_text(" ", strip=True))
        )
    ]
    for paragraph in date_paragraphs:
        year_match = re.search(r"\b(20\d{2})\b", paragraph)
        if year_match is None:
            continue
        year = int(year_match.group(1))
        for day, month_name, _ in DATE_RE.findall(paragraph):
            try:
                event_date = date(year, MONTHS[month_name.lower()], int(day))
            except ValueError:
                continue
            _add(events, seen, counts, "Buurtsport 12+ voor meiden", event_date,
                 location, GIRLS_URL, "recurring")


def _published_date(soup):
    match = re.search(r"Datum:\s*(\d{1,2}\s+\w+\s+\d{4})", soup.get_text(" ", strip=True))
    return _date_from_text(match.group(1)) if match else None


def _section_location(section):
    for item in section.find_all("li"):
        text = item.get_text(" ", strip=True)
        match = re.match(r"Locatie:\s*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _is_gouda_location(location):
    lower = location.casefold()
    return "gouda" in lower or any(venue in lower for venue in GOUDA_VENUES)


def _news_occurrences(soup, url, events, seen, counts):
    main = soup.find("main")
    if main is None:
        return
    published = _published_date(soup)
    for heading in main.find_all("h3"):
        text = heading.get_text(" ", strip=True)
        match = re.match(r"^(.+?\d{1,2}\s+\w+(?:\s+\d{4})?):\s*(.+)$", text)
        if match is None:
            continue
        title = match.group(2).strip()
        lower_title = title.casefold()
        if not any(word in lower_title for word in ACTIVITY_WORDS):
            continue
        if any(word in lower_title for word in NON_PUBLIC_WORDS):
            continue
        event_date = _date_from_text(match.group(1), published)
        location = _section_location(heading.parent)
        if event_date and location and _is_gouda_location(location):
            if "wereld-alzheimer-dag" in url and title.casefold() == "vitaal 55+":
                title = "Vitaal 55+ (Wereld Alzheimer Dag)"
            _add(events, seen, counts, title, event_date, location, url, "one_off")

    # Sommige nieuwsartikelen tonen per buurt een gedateerde lijst in plaats van kopjes.
    if "valbus" not in main.get_text(" ", strip=True).casefold():
        return
    for paragraph in main.find_all("p"):
        date_label = paragraph.get_text(" ", strip=True)
        if DATE_RE.fullmatch(date_label) is None:
            continue
        event_date = _date_from_text(date_label)
        following = paragraph.find_next_sibling("ul")
        if event_date is None or following is None:
            continue
        for item in following.find_all("li"):
            text = item.get_text(" ", strip=True)
            match = re.search(r"Gouda\s+(.+?)\s*-\s*(.+)$", text)
            if match:
                neighborhood, place = match.groups()
                _add(events, seen, counts, f"Valbus Gouda {neighborhood}", event_date,
                     f"{place}, Gouda {neighborhood}", url, "one_off")


def fetch_events(stats=None):
    counts = {
        "source_pages_scanned": 0,
        "raw_candidate_activities": 0,
        "one_off_included": 0,
        "recurring_included": 0,
        "recurring_excluded": 0,
        "source_level_duplicates": 0,
    }
    excluded = []
    events = []
    seen = set()
    with requests.Session() as session:
        _girls_occurrences(_page(session, GIRLS_URL, counts), events, seen, counts)
        for path, reason in UNRELIABLE_SCHEDULES.items():
            url = urljoin(BASE_URL, path)
            soup = _page(session, url, counts)
            heading = soup.find("h1")
            if heading:
                excluded.append({"title": heading.get_text(" ", strip=True), "url": url, "reason": reason})
                counts["recurring_excluded"] += 1

        page_url = NEWS_URL
        visited_pages = set()
        article_urls = set()
        while page_url and page_url not in visited_pages:
            visited_pages.add(page_url)
            soup = _page(session, page_url, counts)
            main = soup.find("main")
            if main is None:
                raise ValueError("SPORT•GOUDA nieuwsindex mist de inhoud.")
            article_urls.update(
                urljoin(page_url, link["href"]) for link in main.select("a[href]")
                if re.search(r"/nieuws/[^/?]+$", link["href"])
            )
            next_link = next(
                (link for link in main.select("a[href]")
                 if link.get_text(" ", strip=True).startswith("Volgende")),
                None,
            )
            page_url = urljoin(page_url, next_link["href"]) if next_link else None

        for url in sorted(article_urls):
            _news_occurrences(_page(session, url, counts), url, events, seen, counts)

    counts["final_event_occurrences"] = len(events)
    counts["excluded_schedules"] = excluded
    if stats is not None:
        stats.update(counts)
    return events
