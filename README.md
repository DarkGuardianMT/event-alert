# Event Alert

Event Alert collects local events from multiple sources around Gouda and nearby cities and presents them in one searchable, filterable website.

This portfolio project demonstrates automation and data processing: collecting external event listings, normalizing them, storing them in MySQL, and presenting them through a PHP API. Categorization is rule-based, not AI-powered.

## Features

- Collection from multiple event sources through separate Python scrapers
- Date normalization and duplicate prevention
- Event lifecycle tracking for active and inactive events
- Deterministic, rule-based classification across nine event categories
- MySQL/MariaDB storage
- PHP JSON API with city, date, and category filters
- Responsive HTML, CSS, and vanilla JavaScript frontend
- Dutch and English language support
- Event detail pages

Seven source modules cover Gemeente Gouda, Cultuurhuis Garenspinnerij, UitGouda, Volksuniversiteit Gouda, SPORT•GOUDA, Chocoladefabriek Gouda, and Gouda Bruist. The pipeline normalizes Dutch dates, explicit times, and description whitespace. Duplicate matching uses title, start date, and city. Failed, empty, or severely incomplete source results cannot deactivate stored events.

## Architecture

```text
Sources
  → Python scrapers
  → normalization / categorization
  → MySQL
  → PHP API
  → HTML/CSS/JavaScript frontend
```

## Tech Stack

- Python
- Requests
- BeautifulSoup
- MySQL / MariaDB
- PHP
- HTML
- CSS
- Vanilla JavaScript

## Project Structure

- `api/` contains the PHP JSON endpoints and database configuration.
- `database/` contains the schema for new databases and incremental migrations.
- `frontend/` contains the responsive website and browser-side behavior.
- `scraper/` contains the collection pipeline, normalizer, categorizer, database synchronization, and source modules.

## Local Setup

The project requires Python, MySQL or MariaDB, and a PHP environment with PDO MySQL support. XAMPP provides a convenient local PHP and MariaDB setup on Windows.

Create and activate a virtual environment, then install the scraper dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r scraper\requirements.txt
```

Create a separate local database named `event_alert` and import `database/schema.sql` using your MySQL client. Apply the schema only to a new, empty database; it includes the category seed data. Existing installations should review and apply only missing files in `database/migrations/` in order. Do not reapply migrations or reset an existing database.

## Environment Variables

The PHP API and Python scraper use the same database environment variables:

- `EVENT_ALERT_DB_HOST`
- `EVENT_ALERT_DB_PORT`
- `EVENT_ALERT_DB_NAME`
- `EVENT_ALERT_DB_USER`
- `EVENT_ALERT_DB_PASSWORD`

The PHP API falls back to XAMPP-compatible local values: `localhost`, port `3306`, database `event_alert`, user `root`, and an empty password. The Python scraper uses the same host, port, and password defaults, but requires `EVENT_ALERT_DB_NAME` and `EVENT_ALERT_DB_USER` to be set explicitly.

`.env.example` contains safe local example values. The actual `.env` file is ignored by Git. The application does not load `.env` files automatically, so export the variables into the scraper process or configure them in the PHP/web-server environment. Production hosting should provide its real database credentials through that environment and must not commit them to the repository.

For the default local XAMPP installation, set the required variables in the same PowerShell session used to start Python and PHP:

```powershell
$env:EVENT_ALERT_DB_NAME = 'event_alert'
$env:EVENT_ALERT_DB_USER = 'root'
```

Set the remaining variables to match your installation. The empty-password root defaults are for local development only; use a dedicated database user and a password for hosting.

## Running the Scraper

Set the database environment variables for your local installation and run the scraper from the repository root:

```powershell
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $venvPython scraper\main.py
```

This command contacts the external sources and writes event and lifecycle changes to the configured database. It is a manual collection job, not a test. Metadata backfills also contact sources, even in preview mode.

## Running Locally

From the repository root, start PHP's development server with the XAMPP PHP executable:

```powershell
C:\xampp\php\php.exe -S 127.0.0.1:8765
```

Open [http://127.0.0.1:8765/frontend/](http://127.0.0.1:8765/frontend/). Apache through XAMPP can also serve the project when the repository is available under `htdocs`, directly or through a directory junction.

The development server is for local use only. Before hosting, configure the web server to expose only the frontend and API and deny access to `.git`, environment files, scraper code, database scripts, and local data. Keep PHP error display disabled on a hosted API.

## Safe Checks

From the repository root, with the virtual environment activated:

```powershell
Remove-Item Env:EVENT_ALERT_RUN_DB_TESTS -ErrorAction SilentlyContinue
python -m unittest discover -s scraper/tests
python -m pip check
Get-ChildItem api -Filter *.php -Recurse | ForEach-Object { php -l $_.FullName }
```

The normalizer, categorizer, and scraper unit tests use in-memory examples and mocked responses; they do not require live scraping. Six category synchronization tests are skipped by default. They perform database writes inside rollback transactions and depend on specific pre-existing event IDs and data. Enable them with `EVENT_ALERT_RUN_DB_TESTS=1` only against a separate disposable database with suitable fixtures, never your working event database. No database reset is needed for the offline tests.

If Node.js is already installed, `node --check frontend/js/common.js`, `node --check frontend/js/app.js`, and `node --check frontend/js/event.js` check JavaScript syntax. Node.js is an optional checking tool, not an application dependency.

## API

- `GET /api/events/` returns active events. Optional filters are `city`, `from`, `to`, and `category`.
- `GET /api/event/?id={id}` returns one active event by ID.

## Categories

Event Alert currently uses nine categories:

- Community
- Sport
- Kids & Family
- Culture
- Workshop
- Lecture
- Market
- Exhibition
- Other

Classification is deterministic and rule-based; it does not use AI.

## Status

Event Alert is an active MVP under development.

It is not verified as production-ready or publicly deployed. Accounts, favorites, email notifications, automatic scheduling, and AI extraction are not implemented. Scrapers depend on external page structures and may miss ambiguous dates or locations; yearless dates currently default to 2026. Category rules can misclassify events, duplicate prevention is application-level, and the API currently has no pagination.

## Source Data

The repository contains code, schema, category seeds, and small test examples; collected event records, database dumps, logs, and source media should remain local. External descriptions and media belong to their respective owners. Review each source's terms and permissions before collecting or redistributing its content. No open-source license has been selected for this project's code yet.

## Roadmap

- Improve data quality
- Prepare production hosting
- Add automated scraper scheduling
- Add event alerts and email notifications
- Add more sources and cities
- Enrich event metadata
