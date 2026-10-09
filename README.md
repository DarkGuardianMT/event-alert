# Event Alert

Event Alert collects local events from websites in Gouda and nearby towns and presents them in one searchable, filterable interface. Python scrapers process event listings, MySQL stores the results, and a PHP API serves the browser frontend.

## Features

- Separate scrapers for seven local event sources
- Normalization of Dutch dates, explicit times, and descriptions
- Duplicate detection using title, start date, and city
- Active and inactive event tracking, with safeguards for failed or incomplete collections
- Rule-based classification into nine event categories
- City, date, and category filters, plus title and location search
- Event detail pages with links to the original source
- Responsive interface with Dutch and English display options

## Technologies and Architecture

- Python with Requests, BeautifulSoup, and MySQL Connector
- PHP with PDO MySQL
- MySQL or MariaDB
- HTML, CSS, and vanilla JavaScript

```text
Source websites -> Python scrapers -> normalization and categorization
                -> MySQL -> PHP JSON API -> browser frontend
```

## Project Structure

- `scraper/` — source modules, processing pipeline, database synchronization, and tests
- `api/` — PHP endpoints and database configuration
- `database/` — schema and incremental migrations
- `frontend/` — event list, detail pages, styles, and JavaScript
- `docs/DEVELOPMENT.md` — detailed setup, testing, and security guidance

## Local Setup

Run these commands from the repository root in PowerShell. You need Python, MySQL or MariaDB, and PHP with PDO MySQL support. XAMPP is one option on Windows; see the [development guide](docs/DEVELOPMENT.md) for configuration details.

1. Create a virtual environment and install the Python dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r scraper\requirements.txt
   ```

2. Create an empty local database named `event_alert` and import [database/schema.sql](database/schema.sql) using your MySQL client. For an existing database, follow the migration guidance in the development guide.

3. Set the database environment variables in the same session. For the default local XAMPP configuration:

   ```powershell
   $env:EVENT_ALERT_DB_NAME = 'event_alert'
   $env:EVENT_ALERT_DB_USER = 'root'
   ```

   See [.env.example](.env.example) for all five variables and adjust them to your installation. `.env` files are not loaded automatically. The empty-password root defaults are for local development only.

4. Start the local PHP server:

   ```powershell
   php -S 127.0.0.1:8765
   ```

   Open [http://127.0.0.1:8765/frontend/](http://127.0.0.1:8765/frontend/). If PHP is not on your PATH, use `C:\xampp\php\php.exe` in place of `php`.

To collect events manually, run `python scraper\main.py` with the virtual environment active. This contacts external sources and writes to the configured database. It is not a test.

## Tests and Checks

With the virtual environment active, run:

```powershell
Remove-Item Env:EVENT_ALERT_RUN_DB_TESTS -ErrorAction SilentlyContinue
python -m unittest discover -s scraper/tests
python -m pip check
Get-ChildItem api -Filter *.php -Recurse | ForEach-Object { php -l $_.FullName }
```

The unit tests use in-memory examples and mocked HTTP responses. Database integration tests are skipped by default; use only a separate disposable database with suitable fixtures. See the [development guide](docs/DEVELOPMENT.md#tests-and-checks) for details and optional JavaScript syntax checks.

## API

- `GET /api/events/` — active events, with optional `city`, `from`, `to`, and `category` filters
- `GET /api/event/?id={id}` — one active event by ID

## Current Status

Event Alert is an MVP under development. Categorization is deterministic and rule-based, with no AI functionality. Accounts, favorites, email notifications, and automatic scheduling are not implemented. Production deployment has not been verified.

Scrapers depend on external page structures and may miss ambiguous dates or locations. Category rules can misclassify events, duplicate prevention is application-level, and the API has no pagination. Further limitations and source-data handling are covered in the development guide.

No open-source license has been selected for the project's code yet.
