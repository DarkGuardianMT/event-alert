from sources.gemeente_gouda import fetch_events as fetch_gouda_events
from sources.garenspinnerij import fetch_events as fetch_garenspinnerij_events
from sources.uitgouda import fetch_events as fetch_uitgouda_events
from sources.volksuniversiteit_gouda import fetch_events as fetch_volksuniversiteit_events


def collect_events():
    events = fetch_gouda_events()
    events.extend(fetch_garenspinnerij_events())
    events.extend(fetch_uitgouda_events())
    events.extend(fetch_volksuniversiteit_events())
    return events
