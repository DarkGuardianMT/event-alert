from collector import collect_events
from database import insert_events
from normalizer import normalize_date


def main():
    print("Event Alert scraper gestart.\n")
    events = collect_events()
    for event in events:
        event.update(normalize_date(event["date_text"]))

    result = insert_events(events)

    print(f"Aantal evenementen: {len(events)}")
    print(f"Nieuwe evenementen: {result['inserted']}")
    print(f"Overgeslagen duplicaten: {result['skipped']}")


if __name__ == "__main__":
    main()
