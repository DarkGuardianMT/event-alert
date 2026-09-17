import argparse

from collector import collect_source_results
from database import backfill_event_metadata
from normalizer import normalize_event


def main():
    parser = argparse.ArgumentParser(description="Vul ontbrekende evenementmetadata veilig aan.")
    parser.add_argument("--apply", action="store_true", help="Sla de aangevulde metadata op.")
    args = parser.parse_args()

    successful, failed = collect_source_results()
    for source, events in list(successful.items()):
        try:
            successful[source] = [normalize_event(event) for event in events]
        except Exception as error:
            failed[source] = str(error)
            del successful[source]

    if not successful:
        raise RuntimeError("Geen bronnen konden veilig worden verwerkt.")

    result = backfill_event_metadata(successful, apply=args.apply)
    print("Modus:", "toepassen" if args.apply else "voorvertoning")
    print("Overeenkomende rijen:", result["matched"])
    print("Rijen met aanvullingen:", result["rows_updated"])
    print("Starttijden:", result["start_times_added"])
    print("Eindtijden:", result["end_times_added"])
    print("Beschrijvingen:", result["descriptions_added"])
    for source, error in failed.items():
        print(f"Bron mislukt (overgeslagen): {source}: {error}")


if __name__ == "__main__":
    main()
