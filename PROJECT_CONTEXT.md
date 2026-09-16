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
- `scraper/database.py` implements MySQL connections, inserts, duplicate checks, lifecycle updates, and event-category link synchronization using `mysql-connector-python`.
- Duplicate matching uses `title`, `start_date`, and `city`; matching events are skipped.
- Duplicate observations refresh `last_seen_at` and reactivate the existing row. New rows start active with a current `last_seen_at` timestamp.
- A successful nonempty scrape may mark unseen rows from that same stored source inactive. Failed, unexpectedly empty, and severely incomplete scrapes cannot deactivate rows. Inactive rows remain stored; events are never deleted.
- `scraper/main.py` collects by source, normalizes dates, syncs lifecycle state, and reports source failures and suspicious results.
- `database/schema.sql` defines the `events` table; `database/migrations/001_event_lifecycle.sql` adds the lifecycle fields to existing databases.
- `database/migrations/002_event_categories.sql` adds `categories` and the many-to-many `event_categories` table and seeds nine stable slugs: `community`, `sport`, `kids_family`, `culture`, `workshop`, `lecture`, `market`, `exhibition`, and `other`.
- `scraper/categorizer.py` assigns one or more categories with deterministic non-AI rules. `scraper/backfill_categories.py` previews or transactionally categorizes all stored events, including inactive rows. New and duplicate observations classify the canonical stored row after the production duplicate match; category changes do not alter lifecycle safety.
- `api/events/index.php` exposes active events and their ordered category arrays as JSON at `GET /api/events/`, with optional exact-city, inclusive `from`/`to` date, and exact `category` slug filters. Invalid filters return HTTP 400. `api/config/database.php` connects through PHP PDO using environment variables and XAMPP-compatible local defaults.
- `api/event/index.php` exposes one active event and its ordered category array by numeric ID at `GET /api/event/?id={id}`. Invalid IDs return HTTP 400; missing and inactive events return HTTP 404.
- `frontend/` contains the first HTML/CSS/vanilla JavaScript browsing interface. It loads event cards and city options from the PHP API, uses the API for city/date filters, and applies title/location search locally. Interface text and displayed dates switch between Dutch (default) and English; the choice is stored under `event-alert-language` in localStorage. Event titles, source names, and city names remain as supplied by the API.
- Each event card opens `frontend/event.html?id={id}` in the same tab. The detail page loads the single-event API, shows its original source link, and shares the list's date formatting and language preference through `frontend/js/common.js`.
- Development uses local MySQL through XAMPP. Database configuration comes from environment variables.

## Not implemented yet

- Accounts, favorites, and alerts.
- Category chips and filtering in the frontend.
- Scheduler or cron.
- AI extraction.

## Next planned step

Add localized category chips and filtering to the frontend.
