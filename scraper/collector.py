from sources.gemeente_gouda import fetch_events as fetch_gouda_events
from sources.garenspinnerij import fetch_events as fetch_garenspinnerij_events
from sources.uitgouda import fetch_events as fetch_uitgouda_events


def collect_events():
    events = fetch_gouda_events()
    events.extend(fetch_garenspinnerij_events())
    events.extend(fetch_uitgouda_events())
    return events
