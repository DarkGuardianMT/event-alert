# Event Alert

## Project overview

Event Alert is a platform for collecting small and medium-sized local community events from multiple websites and presenting them in one place.

The project starts with Gouda. Its intended geographical expansion is first to Zuid-Holland and later to the rest of the Netherlands.

## Event priorities

The first version prioritizes:

- Neighborhood events
- Workshops
- Markets
- Family activities
- Library events
- Cultural activities
- Open days
- Local sports and community activities

Large concerts, stadium events, and large ticketing platforms are not a priority for version 1.

## Technical direction

- Event data may come from APIs as well as regular websites without APIs.
- Python will collect and scrape event data.
- PHP and MySQL will power the website and data storage.
- AI may later help extract structured event data from unstructured articles, but it is not part of the first scraper.

## Initial plan

- First planned source: Gemeente Gouda evenementenkalender.
- First milestone: scrape events from one source and print normalized event data in the terminal.
- No database integration yet.
- No frontend implementation yet.
- No scheduler or cron setup yet.
