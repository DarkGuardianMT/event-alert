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

Verified full local collection on 2026-09-17:

- Gemeente Gouda: 56 events.
- Cultuurhuis Garenspinnerij: 20 events.
- UitGouda: 60 events.
- Volksuniversiteit Gouda: 34 events.
- SPORT•GOUDA: 25 events.
- Chocoladefabriek Gouda: 6 events.
- Gouda Bruist: 82 safe candidates, of which 80 are stored under that source because two matched existing cross-source identities.
- The local MySQL database contains 448 rows: 435 active and 13 inactive.

These counts are a snapshot and may change as the source calendars are updated.

## Current architecture

- Python source modules in `scraper/sources/` collect raw events using requests and BeautifulSoup.
- `scraper/collector.py` records successful and failed source scrapes separately; its combined-list function remains available.
- `scraper/normalizer.py` normalizes Dutch date text into `start_date` and `end_date`, and explicit clock text into nullable `start_time` and `end_time` values. It also normalizes whitespace and limits stored source descriptions to 2,000 characters. The original `date_text` remains preserved.
- `scraper/database.py` implements MySQL connections, inserts, duplicate checks, lifecycle updates, and event-category link synchronization using `mysql-connector-python`.
- Duplicate matching uses `title`, `start_date`, and `city`; matching events are skipped.
- Duplicate observations refresh `last_seen_at` and reactivate the existing row. New rows start active with a current `last_seen_at` timestamp.
- A successful nonempty scrape may mark unseen rows from that same stored source inactive. Failed, unexpectedly empty, and severely incomplete scrapes cannot deactivate rows. Inactive rows remain stored; events are never deleted.
- `scraper/main.py` collects by source, normalizes dates and richer metadata, syncs lifecycle state, and reports source failures and suspicious results.
- `database/schema.sql` defines the `events` table; `database/migrations/001_event_lifecycle.sql` adds the lifecycle fields to existing databases.
- `database/migrations/002_event_categories.sql` adds `categories` and the many-to-many `event_categories` table and seeds nine stable slugs: `community`, `sport`, `kids_family`, `culture`, `workshop`, `lecture`, `market`, `exhibition`, and `other`.
- `database/migrations/003_event_metadata.sql` adds nullable `start_time`, `end_time`, and `description` fields. Duplicate identity remains `title`, `start_date`, and `city`. New rows store available metadata; same-source duplicates fill missing metadata without replacing useful stored values or changing lifecycle rules.
- `scraper/categorizer.py` assigns one or more categories with deterministic non-AI rules. `scraper/backfill_categories.py` previews or transactionally categorizes all stored events, including inactive rows. New and duplicate observations classify the canonical stored row after the production duplicate match; category changes do not alter lifecycle safety.
- A category quality audit added conservative rules for explicit performance and music wording, community titles such as `Yap & Yarn` and `Gouda bij Kaarslicht`, youth and compound tournament wording, and exact Volksuniversiteit `/kunst-cultuur/` and `/culinair/` URL sections. Across all 329 stored events, `other` decreased from 159 (48.33%) to 103 (31.31%); active `other` decreased from 156 to 100. Classification remains deterministic and non-AI. Opaque film, theatre, party, festival, lifestyle, and course titles intentionally remain `other` when the stored fields do not provide reliable evidence.
- A controlled metadata-only backfill preserves row counts, active flags, and lifecycle timestamps. The 2026-09-17 local backfill populated 79 start times, 44 end times, and 71 descriptions across 329 stored rows. Stored coverage by source is: Gemeente Gouda 0/0/0, Garenspinnerij 0/0/17, UitGouda 23/23/0, Volksuniversiteit Gouda 34/0/34, SPORT•GOUDA 21/21/19, and Chocoladefabriek Gouda 1/0/1 for start time/end time/description.
- Source extraction stays conservative. Gemeente Gouda has no reliable richer metadata; Garenspinnerij uses listing excerpts; UitGouda accepts times only when visible card time agrees with structured data; Volksuniversiteit uses its single-session time and event body; SPORT•GOUDA accepts only unambiguous explicit ranges and the recurring girls activity description; Chocoladefabriek uses its detail header time and event-specific content. Missing fields remain null, duration text is not converted into an invented end time, and descriptions are never generated or summarized with AI.
- Gouda Bruist is the seventh source. Its scraper keeps a persistent session for the initial listing and POST/AJAX pagination, caches activity details by activity ID, and caches linked location pages by location ID. It accepts only explicitly verified Gouda locations and excludes unresolved, outside-Gouda, and online-only activities. Listing day/month values receive a year only when explicit detail-page bounds make the result unambiguous; weekday-only recurrence text is never expanded. Discrete recurring sessions become one row per explicit card, while an explicit multi-day `Tentoonstelling` with consistent times becomes one ranged event. A live 2026-09-17 run scanned 910 cards and 313 details, excluded 343 unresolved-city cards, 8 online cards, and 362 otherwise eligible cards without safe year bounds, collapsed 7 continuous ranges covering 122 listing cards, and retained 72 explicit occurrences from 5 discrete recurring activities. The resulting 82 candidates had 82 start times, 80 safe end times, and 82 descriptions. Source health checks reject runs below 500 raw cards, 150 activity IDs, or 60 final candidates before lifecycle synchronization.
- `api/events/index.php` exposes active events, nullable start/end times, and ordered category arrays as JSON at `GET /api/events/`, with optional exact-city, inclusive `from`/`to` date, and exact `category` slug filters. Descriptions stay out of the list response to keep it compact. Invalid filters return HTTP 400. `api/config/database.php` connects through PHP PDO using environment variables and XAMPP-compatible local defaults.
- `api/event/index.php` exposes one active event, nullable start/end times, its full nullable source description, and its ordered category array by numeric ID at `GET /api/event/?id={id}`. Invalid IDs return HTTP 400; missing and inactive events return HTTP 404.
- `frontend/` contains the HTML/CSS/vanilla JavaScript browsing interface. It builds city and category options from the unfiltered active-event response, uses the API for city/date/category filters, and applies title/location search locally. Event cards show up to three category chips, while detail pages show every category.
- Interface text, displayed dates, category options, and category chips switch between Dutch (default) and English using the API's localized category names. The choice is stored under `event-alert-language` in localStorage. Event titles, source names, city names, and locations remain as supplied by the API.
- Each event card opens `frontend/event.html?id={id}` in the same tab. Cards append available times to the localized date without empty placeholders. The detail page loads the single-event API, shows an available time range and source-language description, hides the description section when empty, and shows all category chips and its original source link. Shared formatting and language preference remain in `frontend/js/common.js`; source descriptions are not translated.
- Development uses local MySQL through XAMPP. PHP and Python share the `EVENT_ALERT_DB_HOST`, `EVENT_ALERT_DB_PORT`, `EVENT_ALERT_DB_NAME`, `EVENT_ALERT_DB_USER`, and `EVENT_ALERT_DB_PASSWORD` configuration names.
- The PHP API retains XAMPP-compatible local defaults. The Python scraper requires the database name and user while defaulting the local host, port, and empty password. Production hosting must inject real credentials through its process or web-server environment; the application does not require or automatically load dotenv files. `.env` remains ignored, and `.env.example` documents safe local values.

## Not implemented yet

- Accounts, favorites, and alerts.
- Scheduler or cron.
- AI extraction.

## Next planned step

Prepare the completed category-enabled MVP for deployment and continue with accounts, favorites, or alerts when prioritized.
