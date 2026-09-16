# Event Alert

Event Alert collects local events from multiple sources around Gouda and nearby cities and presents them in one searchable, filterable website.

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

Create a database named `event_alert`. For a new installation, apply `database/schema.sql`. Existing installations should apply the relevant files in `database/migrations/` in order.

Database configuration is supplied through environment variables. The scraper requires `EVENT_ALERT_DB_NAME` and `EVENT_ALERT_DB_USER`; `EVENT_ALERT_DB_HOST`, `EVENT_ALERT_DB_PORT`, and `EVENT_ALERT_DB_PASSWORD` are optional. The PHP API uses the same variables and has XAMPP-compatible local defaults.

## Running the Scraper

Set the database environment variables for your local installation and run the scraper from the repository root:

```powershell
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $venvPython scraper\main.py
```

## Running Locally

From the repository root, start PHP's development server with the XAMPP PHP executable:

```powershell
C:\xampp\php\php.exe -S 127.0.0.1:8765
```

Open [http://127.0.0.1:8765/frontend/](http://127.0.0.1:8765/frontend/). Apache through XAMPP can also serve the project when the repository is available under `htdocs`, directly or through a directory junction.

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

## Roadmap

- Improve data quality
- Prepare production hosting
- Add automated scraper scheduling
- Add event alerts and email notifications
- Add more sources and cities
- Enrich event metadata
