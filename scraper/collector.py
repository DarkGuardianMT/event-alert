from sources.gemeente_gouda import fetch_events as fetch_gouda_events
from sources.garenspinnerij import fetch_events as fetch_garenspinnerij_events


def collect_events():
    events = fetch_gouda_events()
    events.extend(fetch_garenspinnerij_events())
    return events
