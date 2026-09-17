from sources.gemeente_gouda import fetch_events as fetch_gouda_events
from sources.garenspinnerij import fetch_events as fetch_garenspinnerij_events
from sources.uitgouda import fetch_events as fetch_uitgouda_events
from sources.volksuniversiteit_gouda import fetch_events as fetch_volksuniversiteit_events
from sources.sportpunt_gouda import fetch_events as fetch_sportpunt_events
from sources.chocoladefabriek import fetch_events as fetch_chocoladefabriek_events
from sources.gouda_bruist import fetch_events as fetch_gouda_bruist_events


SOURCES = (
    ("Gemeente Gouda", fetch_gouda_events),
    ("Cultuurhuis Garenspinnerij", fetch_garenspinnerij_events),
    ("UitGouda", fetch_uitgouda_events),
    ("Volksuniversiteit Gouda", fetch_volksuniversiteit_events),
    ("SPORT•GOUDA", fetch_sportpunt_events),
    ("Chocoladefabriek Gouda", fetch_chocoladefabriek_events),
    ("Gouda Bruist", fetch_gouda_bruist_events),
)


def collect_source_results(sources=SOURCES):
    successful = {}
    failed = {}
    for name, fetch in sources:
        try:
            events = fetch()
            if not isinstance(events, list) or any(
                not isinstance(event, dict)
                or event.get("source") != name
                or not event.get("title")
                or not isinstance(event.get("date_text"), str)
                for event in events
            ):
                raise ValueError("Bron leverde ongeldige evenementen op.")
            successful[name] = events
        except Exception as error:
            # Een mislukte bron ontbreekt in de succesvolle resultaten.
            failed[name] = str(error)
    return successful, failed


def collect_events():
    successful, failed = collect_source_results()
    if failed:
        raise RuntimeError("Mislukte bronnen: " + ", ".join(failed))
    return [event for events in successful.values() for event in events]
