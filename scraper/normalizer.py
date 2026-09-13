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
