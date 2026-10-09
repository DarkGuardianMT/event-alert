import re
from collections import defaultdict
from datetime import date, time
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from sources.http import SourceSession


BASE_URL = "https://goudabruist.nl"
LISTING_URL = f"{BASE_URL}/activiteiten"
SOURCE = "Gouda Bruist"
PAGE_SIZE = 40
MAX_PAGES = 100
TIMEOUT = 30
MIN_RAW_LISTING_CARDS = 500
MIN_ACTIVITY_IDS = 150
MIN_FINAL_EVENTS = 60
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/140 Safari/537.36"
)
AJAX_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": LISTING_URL,
    "Accept": "text/plain, */*; q=0.01",
}
MONTHS = {
    "jan": 1, "feb": 2, "mrt": 3, "apr": 4, "mei": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12,
}
MONTH_NAMES = (
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
)
DATE_RE = re.compile(
    r"(?:(?:ma|di|wo|do|vr|za|zo)\s+)?"
    r"(\d{1,2})\s+(jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)\s+(\d{4})",
    re.IGNORECASE,
)
TIME_RE = re.compile(
    r"^\s*([01]?\d|2[0-3]):([0-5]\d)"
    r"(?:\s*[-\N{EN DASH}\N{EM DASH}]\s*([01]?\d|2[0-3]):([0-5]\d))?\s*$"
)
OUTSIDE_CITY_RE = re.compile(
    r"\b(?:Waddinxveen|Haastrecht|Bodegraven|Reeuwijk|Zevenhuizen|Moordrecht|"
    r"Schoonhoven|Rotterdam|Schiedam|Zoetermeer|Wassenaar|Utrecht)\b",
    re.IGNORECASE,
)


def _activity_id(url):
    query_id = (parse_qs(urlparse(url).query).get("id") or [""])[0]
    if query_id:
        return query_id
    match = re.search(r"/activiteit/(\d+)(?:/|$)", urlparse(url).path)
    return match.group(1) if match else ""


def _location_id(url):
    query_id = (parse_qs(urlparse(url).query).get("id") or [""])[0]
    if query_id:
        return query_id
    match = re.search(r"/locatie/(\d+)(?:/|$)", urlparse(url).path)
    return match.group(1) if match else ""


def _parse_card(card):
    title_element = card.select_one(".go_card-title-wrapper")
    day_element = card.select_one(".go_date-day-wrapper")
    month_element = card.select_one(".go_date-month-wrapper")
    if title_element is None or day_element is None or month_element is None:
        return None

    url = urljoin(BASE_URL, card.get("href", ""))
    activity_id = _activity_id(url)
    month = MONTHS.get(month_element.get_text(" ", strip=True).casefold()[:3])
    try:
        day = int(day_element.get_text(" ", strip=True))
    except ValueError:
        return None
    if not activity_id or month is None or not 1 <= day <= 31:
        return None

    time_element = card.select_one(".go_date-time-wrapper")
    location_element = card.select_one(".go_card-meta-line span")
    return {
        "activity_id": activity_id,
        "engine_url": url,
        "title": title_element.get_text(" ", strip=True),
        "day": day,
        "month": month,
        "time_text": time_element.get_text(" ", strip=True) if time_element else "",
        "location": location_element.get_text(" ", strip=True) if location_element else "",
    }


def _card_key(card):
    return (
        card["activity_id"], card["title"].casefold(), card["day"], card["month"],
        card["time_text"], card["location"].casefold(),
    )


def _listing_cards(session, counts):
    response = session.get(LISTING_URL, timeout=TIMEOUT)
    response.raise_for_status()
    all_cards = []
    seen_cards = set()
    seen_pages = set()

    for page_number in range(MAX_PAGES):
        if page_number:
            offset = page_number * PAGE_SIZE
            response = session.post(
                f"{LISTING_URL}?from={offset}&increment={PAGE_SIZE}",
                headers=AJAX_HEADERS,
                data="",
                timeout=TIMEOUT,
            )
            response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        nodes = soup.select(".go_card-activity")
        counts["listing_pages"] += 1
        counts["raw_listing_cards"] += len(nodes)
        if not nodes:
            break

        page_signature = tuple(node.get("href", "") for node in nodes)
        if page_signature in seen_pages:
            counts["pagination_loops_prevented"] += 1
            break
        seen_pages.add(page_signature)

        new_cards = 0
        for node in nodes:
            card = _parse_card(node)
            if card is None:
                counts["excluded_invalid_listing"] += 1
                continue
            key = _card_key(card)
            if key in seen_cards:
                counts["raw_listing_duplicates"] += 1
                continue
            seen_cards.add(key)
            all_cards.append(card)
            new_cards += 1

        if len(nodes) < PAGE_SIZE or not new_cards:
            break
    else:
        raise ValueError("Gouda Bruist-paginering overschreed de veiligheidslimiet.")

    if not all_cards:
        raise ValueError("Geen Gouda Bruist-activiteitenkaarten gevonden.")
    counts["deduplicated_listing_cards"] = len(all_cards)
    return all_cards


def _meta_values(soup):
    values = {}
    header = soup.select_one("article.go_wall-card-content header")
    if header is None:
        return values
    for line in header.select(".go_card-meta-line"):
        icon = line.select_one("i[title]")
        value = line.select_one("span")
        if icon is not None and value is not None:
            values[icon["title"]] = value.get_text(" ", strip=True)
    return values


def _date_bounds(value):
    matches = list(DATE_RE.finditer(value or ""))
    if not matches:
        return None
    parsed = []
    for match in matches[:2]:
        try:
            parsed.append(date(int(match.group(3)), MONTHS[match.group(2).casefold()], int(match.group(1))))
        except ValueError:
            return None
    end = parsed[-1]
    return (parsed[0], end) if end >= parsed[0] else None


def _description(soup):
    paragraphs = soup.select(
        "article.go_wall-card-content "
        ".go_wall-card-main-module-wrapper .go_wall-card-module > p"
    )
    value = " ".join(paragraph.get_text(" ", strip=True) for paragraph in paragraphs)
    return " ".join(value.split()) or None


def _properties(soup):
    properties = {}
    for wrapper in soup.select("article.go_wall-card-content .go_property"):
        label = wrapper.select_one("dt")
        value = wrapper.select_one("dd")
        if label is not None and value is not None:
            properties[label.get_text(" ", strip=True).casefold()] = value.get_text(" ", strip=True)
    return properties


def _fetch_detail(session, card, counts):
    response = session.get(card["engine_url"], timeout=TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    bounds = _date_bounds(_meta_values(soup).get("Datum", ""))
    if bounds is None:
        counts["details_without_date_bounds"] += 1
    location_link = soup.select_one(".go_card-location[href]")
    location_url = urljoin(response.url, location_link["href"]) if location_link else ""
    counts["detail_pages_fetched"] += 1
    return {
        "url": response.url,
        "start_date": bounds[0] if bounds else None,
        "end_date": bounds[1] if bounds else None,
        "description": _description(soup),
        "detail_location": _meta_values(soup).get("Locatie", ""),
        "location_id": _location_id(location_url),
        "location_url": location_url,
        "properties": _properties(soup),
    }


def _details_by_activity(session, cards, counts):
    details = {}
    for card in cards:
        activity_id = card["activity_id"]
        if activity_id not in details:
            details[activity_id] = _fetch_detail(session, card, counts)
    counts["distinct_activity_ids"] = len(details)
    return details


def _fetch_location(session, url, counts):
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    venue = soup.select_one("article.go_wall-card-content header h1")
    address = soup.select_one("article.go_wall-card-content header .go_adress-wrapper")
    address_text = address.get_text(" ", strip=True) if address else ""
    city = address_text.rsplit(",", 1)[-1].strip() if "," in address_text else ""
    counts["location_pages_fetched"] += 1
    return {
        "url": response.url,
        "venue": venue.get_text(" ", strip=True) if venue else "",
        "address": address_text,
        "city": city,
    }


def _locations_by_id(session, details, counts):
    locations = {}
    for detail in details.values():
        location_id = detail["location_id"]
        if location_id and location_id not in locations:
            locations[location_id] = _fetch_location(
                session, detail["location_url"], counts
            )
    counts["location_ids"] = len(locations)
    return locations


def _location_status(cards, detail, location):
    texts = [
        *(card["location"] for card in cards),
        detail.get("detail_location", ""),
        location.get("venue", ""),
        location.get("address", ""),
    ]
    combined = " ".join(value for value in texts if value)
    if re.search(r"\bonline\b", combined, re.IGNORECASE):
        return "online"

    city = location.get("city", "").strip()
    if city:
        return "gouda" if city.casefold() == "gouda" else "outside"
    if re.search(r"\bGouda\b", combined, re.IGNORECASE):
        return "gouda"
    if OUTSIDE_CITY_RE.search(combined):
        return "outside"
    return "unresolved"


def _event_location(card, detail, location):
    return (
        card.get("location")
        or detail.get("detail_location")
        or location.get("venue")
        or location.get("address")
        or ""
    )


def _resolve_occurrence_date(day, month, start_date, end_date):
    candidates = []
    for year in range(start_date.year, end_date.year + 1):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if start_date <= candidate <= end_date:
            candidates.append(candidate)
    return candidates[0] if len(candidates) == 1 else None


def _time_text(value, counts):
    match = TIME_RE.fullmatch(value or "")
    if match is None:
        return None
    start = time(int(match.group(1)), int(match.group(2)))
    start_text = start.strftime("%H:%M")
    if match.group(3) is None:
        return start_text
    end = time(int(match.group(3)), int(match.group(4)))
    if end <= start:
        counts["suspicious_time_ranges"] += 1
        return start_text
    return f"{start_text} - {end.strftime('%H:%M')}"


def _date_text(start_date, end_date=None):
    def display(value):
        return f"{value.day} {MONTH_NAMES[value.month - 1]} {value.year}"
    if end_date is not None and end_date != start_date:
        return f"{display(start_date)} - {display(end_date)}"
    return display(start_date)


def _is_continuous_range(detail, cards):
    if detail["start_date"] is None or detail["end_date"] is None:
        return False
    if detail["start_date"] == detail["end_date"]:
        return False
    event_type = detail["properties"].get("type", "").casefold()
    if "tentoonstelling" not in event_type:
        return False
    return len({card["time_text"] for card in cards}) == 1


def _event(card, detail, location, start_date, end_date=None, counts=None):
    return {
        "title": card["title"],
        "date_text": _date_text(start_date, end_date),
        "time_text": _time_text(card["time_text"], counts),
        "description": detail["description"],
        "location": _event_location(card, detail, location),
        "city": "Gouda",
        "source": SOURCE,
        "source_url": detail["url"],
    }


def _build_events(cards, details, locations, counts):
    grouped = defaultdict(list)
    for card in cards:
        grouped[card["activity_id"]].append(card)

    events = []
    seen = set()
    for activity_id, activity_cards in grouped.items():
        detail = details[activity_id]
        location = locations.get(detail["location_id"], {})
        status = _location_status(activity_cards, detail, location)
        if status != "gouda":
            counter = {
                "unresolved": "excluded_unresolved_city",
                "outside": "excluded_outside_gouda",
                "online": "excluded_online",
            }[status]
            counts[counter] += len(activity_cards)
            continue

        if detail["start_date"] is None or detail["end_date"] is None:
            counts["excluded_ambiguous_date"] += len(activity_cards)
            continue

        if _is_continuous_range(detail, activity_cards):
            event = _event(
                activity_cards[0], detail, location,
                detail["start_date"], detail["end_date"], counts,
            )
            counts["collapsed_continuous_ranges"] += 1
            counts["collapsed_listing_cards"] += len(activity_cards)
            candidates = [(event, detail["start_date"])]
        else:
            candidates = []
            for card in activity_cards:
                occurrence_date = _resolve_occurrence_date(
                    card["day"], card["month"],
                    detail["start_date"], detail["end_date"],
                )
                if occurrence_date is None:
                    counts["excluded_ambiguous_date"] += 1
                    continue
                candidates.append((
                    _event(card, detail, location, occurrence_date, counts=counts),
                    occurrence_date,
                ))
            if len(activity_cards) > 1:
                counts["discrete_recurring_activity_ids"] += 1
                counts["discrete_recurring_occurrences"] += len(candidates)

        for event, start_date in candidates:
            key = (event["title"].casefold(), start_date.isoformat(), event["city"].casefold())
            if key in seen:
                counts["source_level_duplicates"] += 1
                continue
            seen.add(key)
            events.append(event)
    return events


def _ensure_healthy(counts):
    if counts["raw_listing_cards"] < MIN_RAW_LISTING_CARDS:
        raise ValueError("Gouda Bruist leverde verdacht weinig activiteitenkaarten op.")
    if counts["distinct_activity_ids"] < MIN_ACTIVITY_IDS:
        raise ValueError("Gouda Bruist leverde verdacht weinig activiteitdetails op.")
    if counts["final_event_occurrences"] < MIN_FINAL_EVENTS:
        raise ValueError("Gouda Bruist leverde verdacht weinig bruikbare evenementen op.")


def fetch_events(stats=None):
    counts = {
        "listing_pages": 0,
        "raw_listing_cards": 0,
        "raw_listing_duplicates": 0,
        "deduplicated_listing_cards": 0,
        "excluded_invalid_listing": 0,
        "pagination_loops_prevented": 0,
        "distinct_activity_ids": 0,
        "detail_pages_fetched": 0,
        "details_without_date_bounds": 0,
        "location_ids": 0,
        "location_pages_fetched": 0,
        "excluded_unresolved_city": 0,
        "excluded_outside_gouda": 0,
        "excluded_online": 0,
        "excluded_ambiguous_date": 0,
        "collapsed_continuous_ranges": 0,
        "collapsed_listing_cards": 0,
        "discrete_recurring_activity_ids": 0,
        "discrete_recurring_occurrences": 0,
        "source_level_duplicates": 0,
        "suspicious_time_ranges": 0,
        "final_event_occurrences": 0,
    }
    with SourceSession(BASE_URL) as session:
        session.headers.update({"User-Agent": USER_AGENT})
        cards = _listing_cards(session, counts)
        details = _details_by_activity(session, cards, counts)
        locations = _locations_by_id(session, details, counts)
        events = _build_events(cards, details, locations, counts)

    counts["final_event_occurrences"] = len(events)
    counts["start_time_count"] = sum(bool(event["time_text"]) for event in events)
    counts["end_time_count"] = sum(
        bool(event["time_text"] and " - " in event["time_text"]) for event in events
    )
    counts["description_count"] = sum(bool(event["description"]) for event in events)
    if stats is not None:
        stats.update(counts)
    _ensure_healthy(counts)
    return events
