from sources.gemeente_gouda import fetch_events


def main():
    print("Event Alert scraper gestart.\n")
    events = fetch_events()
    for number, event in enumerate(events, start=1):
        print(f"{number}. {event['title']}")
        print(f"   Datum: {event['date_text']}")
        print(f"   Locatie: {event['location']}")
        print(f"   Bron: {event['source']}\n")

    print(f"Aantal evenementen: {len(events)}")


if __name__ == "__main__":
    main()
