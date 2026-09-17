from collector import collect_source_results
from database import sync_events
from normalizer import normalize_event


def main():
    print("Event Alert scraper gestart.\n")
    successful, failed = collect_source_results()
    for source, events in list(successful.items()):
        try:
            successful[source] = [normalize_event(event) for event in events]
            events = successful[source]
            if any(not event.get("start_date") for event in events):
                raise ValueError("Een of meer datums konden niet worden genormaliseerd.")
        except Exception as error:
            # Onbetrouwbare datums mogen geen bron-afsluiting veroorzaken.
            failed[source] = str(error)
            del successful[source]

    if not successful:
        print("Geen succesvol verwerkte bronnen.")
        return
    result = sync_events(successful)

    print(f"Aantal evenementen: {sum(len(events) for events in successful.values())}")
    print(f"Nieuwe evenementen: {result['inserted']}")
    print(f"Overgeslagen duplicaten: {result['skipped']}")
    print(f"Vernieuwde evenementen: {result['refreshed']}")
    print(f"Inactief gemarkeerd: {result['deactivated']}")
    for source, error in failed.items():
        print(f"Bron mislukt (niet gedeactiveerd): {source}: {error}")
    for source in result["zero_sources"]:
        print(f"Bron onverwacht leeg (niet gedeactiveerd): {source}")
    for source in result["low_coverage_sources"]:
        print(f"Bron met lage dekking (niet gedeactiveerd): {source}")


if __name__ == "__main__":
    main()
