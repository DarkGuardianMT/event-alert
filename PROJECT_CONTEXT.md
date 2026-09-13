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

## Active sources and collection

Verified local collection on 2026-09-13:

- Gemeente Gouda evenementenkalender: 46 events.
- Cultuurhuis Garenspinnerij: 17 events after source-level duplicate removal.
- Combined: 63 fetched events and 62 unique rows stored in the local MySQL database.

These counts are a snapshot and may change as the source calendars are updated.

## Current architecture

- Python source modules in `scraper/sources/` collect raw events using requests and BeautifulSoup.
- `scraper/collector.py` calls the source modules and combines their events.
- `scraper/normalizer.py` normalizes Dutch date text into `start_date` and `end_date`, preserving the original `date_text`.
- `scraper/database.py` implements MySQL connections, inserts, and duplicate checks using `mysql-connector-python`.
- Duplicate matching uses `title`, `start_date`, and `city`; matching events are skipped.
- `scraper/main.py` collects, normalizes, stores events, and reports fetched, inserted, and skipped counts.
- `database/schema.sql` defines the initial `events` table.
- Development uses local MySQL through XAMPP. Database configuration comes from environment variables.

## Not implemented yet

- PHP frontend.
- Scheduler or cron.
- AI extraction.

## Next planned step

Add a third Gouda community-event source.
