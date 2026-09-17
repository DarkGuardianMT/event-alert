import re
from datetime import date


EVENT_YEAR = 2026
MONTHS = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}
DATE_PATTERN = (
    r"(?:(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\s+)?"
    r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")(?:\s+(\d{4}))?"
)
TIME_PATTERN = re.compile(
    r"^\s*([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*(?:uur|u))?"
    r"(?:\s*(?:-|–|—|tot)\s*([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*(?:uur|u))?)?\s*$",
    re.IGNORECASE,
)


def normalize_date(date_text):
    empty_dates = {"start_date": "", "end_date": ""}
    if not isinstance(date_text, str):
        return empty_dates

    parts = re.split(r"\s*[–—-]\s*|\s+en\s+", date_text.strip().lower())
    if len(parts) not in (1, 2):
        return empty_dates

    dates = []
    try:
        for part in parts:
            match = re.fullmatch(DATE_PATTERN, part)
            if match is None:
                return empty_dates

            day = int(match.group(1))
            month = MONTHS[match.group(2)]
            explicit_year = match.group(3)
            year = int(explicit_year) if explicit_year else (dates[0].year if dates else EVENT_YEAR)
            # Een periode van december naar januari eindigt in het volgende jaar.
            if not explicit_year and dates and month < dates[0].month:
                year += 1
            dates.append(date(year, month, day))
    except ValueError:
        return empty_dates

    if dates[-1] < dates[0]:
        return empty_dates

    return {
        "start_date": dates[0].isoformat(),
        "end_date": dates[-1].isoformat(),
    }


def normalize_time(time_text):
    if not time_text:
        return {"start_time": None, "end_time": None}

    match = TIME_PATTERN.fullmatch(str(time_text))
    if match is None:
        return {"start_time": None, "end_time": None}

    start_hour, start_minute, end_hour, end_minute = match.groups()
    result = {"start_time": f"{int(start_hour):02d}:{start_minute}:00", "end_time": None}
    if end_hour is not None:
        result["end_time"] = f"{int(end_hour):02d}:{end_minute}:00"
    return result


def normalize_description(description, max_length=2000):
    if not description:
        return None
    value = " ".join(str(description).split())
    if not value:
        return None
    if len(value) <= max_length:
        return value
    shortened = value[:max_length + 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return shortened + "…"


def normalize_event(event):
    normalized = dict(event)
    normalized.update(normalize_date(normalized["date_text"]))
    normalized.update(normalize_time(normalized.pop("time_text", None)))
    normalized["description"] = normalize_description(normalized.get("description"))
    return normalized
