from sources.gemeente_gouda import fetch_events


def main():
    print("Event Alert scraper gestart.")
    events = fetch_events()
    print(f"Aantal evenementen: {len(events)}")


if __name__ == "__main__":
    main()
