from database import insert_events
from normalizer import normalize_date
from sources.gemeente_gouda import fetch_events


def main():
    print("Event Alert scraper gestart.\n")
    events = fetch_events()
    for event in events:
        event.update(normalize_date(event["date_text"]))

    inserted = insert_events(events)

    for number, event in enumerate(events, start=1):
        print(f"{number}. {event['title']}")
        print(f"   Datum: {event['date_text']}")
        print(f"   Startdatum: {event['start_date']}")
        print(f"   Einddatum: {event['end_date']}")
        print(f"   Locatie: {event['location']}")
        print(f"   Bron: {event['source']}\n")

    print(f"Aantal evenementen: {len(events)}")
    print(f"Aantal ingevoegde evenementen: {inserted}")


if __name__ == "__main__":
    main()
