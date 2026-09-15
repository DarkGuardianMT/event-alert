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
- `scraper/collector.py` records successful and failed source scrapes separately; its combined-list function remains available.
- `scraper/normalizer.py` normalizes Dutch date text into `start_date` and `end_date`, preserving the original `date_text`.
- `scraper/database.py` implements MySQL connections, inserts, duplicate checks, and lifecycle updates using `mysql-connector-python`.
- Duplicate matching uses `title`, `start_date`, and `city`; matching events are skipped.
- Duplicate observations refresh `last_seen_at` and reactivate the existing row. New rows start active with a current `last_seen_at` timestamp.
- A successful nonempty scrape may mark unseen rows from that same stored source inactive. Failed, unexpectedly empty, and severely incomplete scrapes cannot deactivate rows. Inactive rows remain stored; events are never deleted.
- `scraper/main.py` collects by source, normalizes dates, syncs lifecycle state, and reports source failures and suspicious results.
- `database/schema.sql` defines the `events` table; `database/migrations/001_event_lifecycle.sql` adds the lifecycle fields to existing databases.
- `api/events/index.php` exposes active events as JSON at `GET /api/events/`, with optional exact-city and inclusive `from`/`to` date filters. Results are ordered by start date and title; invalid date filters return HTTP 400. `api/config/database.php` connects through PHP PDO using environment variables and XAMPP-compatible local defaults.
- Development uses local MySQL through XAMPP. Database configuration comes from environment variables.

## Not implemented yet

- PHP frontend.
- Scheduler or cron.
- AI extraction.

## Next planned step

Add a third Gouda community-event source.
