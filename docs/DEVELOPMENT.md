# Development Guide

This guide covers local configuration, safe checks, and precautions for collecting data or preparing a hosted deployment. Start with the basic setup in the [README](../README.md).

## Local Database Setup

Use Python, PHP with PDO MySQL support, and MySQL or MariaDB. XAMPP provides PHP and MariaDB for local development on Windows.

For a new installation, create an empty `event_alert` database and import [schema.sql](../database/schema.sql) through your MySQL client. The schema includes the event tables, lifecycle and metadata columns, category tables, and category seeds.

For an existing installation, inspect its schema first and apply only missing migrations in order:

1. [001_event_lifecycle.sql](../database/migrations/001_event_lifecycle.sql)
2. [002_event_categories.sql](../database/migrations/002_event_categories.sql)
3. [003_event_metadata.sql](../database/migrations/003_event_metadata.sql)

The migrations are one-time changes, not repeatable setup scripts. Do not import the full schema into an existing database, reapply migrations, or reset existing event data. A fresh schema already contains these changes.

## Environment Configuration

The PHP API and Python scraper share these environment variables:

| Variable | Local default | Notes |
| --- | --- | --- |
| `EVENT_ALERT_DB_HOST` | `localhost` | Database host |
| `EVENT_ALERT_DB_PORT` | `3306` | Database port |
| `EVENT_ALERT_DB_NAME` | PHP: `event_alert` | Required explicitly by Python |
| `EVENT_ALERT_DB_USER` | PHP: `root` | Required explicitly by Python |
| `EVENT_ALERT_DB_PASSWORD` | Empty | Set to match your database user |

[.env.example](../.env.example) contains local example values. Actual `.env` files are ignored by Git, but the application does not load them automatically. Export variables into the process environment or configure them in your PHP/web-server environment.

For local XAMPP defaults, use the same PowerShell session to configure and start the application:

```powershell
$env:EVENT_ALERT_DB_HOST = 'localhost'
$env:EVENT_ALERT_DB_PORT = '3306'
$env:EVENT_ALERT_DB_NAME = 'event_alert'
$env:EVENT_ALERT_DB_USER = 'root'
```

Configure `EVENT_ALERT_DB_PASSWORD` securely if your local database requires it. Never put real credentials in tracked files or documentation. The empty-password root defaults are for local development only; hosting requires a dedicated database user and a password supplied through the environment.

## Running Locally

From the repository root, with the virtual environment active, start PHP:

```powershell
php -S 127.0.0.1:8765
```

If PHP is not on your PATH, use `C:\xampp\php\php.exe` instead. Open [http://127.0.0.1:8765/frontend/](http://127.0.0.1:8765/frontend/).

Apache through XAMPP can also serve the repository under `htdocs`, directly or through a directory junction. Its PHP process needs the same environment configuration; variables set in a PowerShell session do not automatically configure an already-running Apache service.

The PHP development server is for local use only. Before hosting, configure the web server to expose only the frontend and API and deny access to `.git`, environment files, scraper code, database scripts, documentation, and local data. Disable PHP error display on the hosted API. The repository has not been verified as production-ready.

## Collection and Backfills

Run a manual collection with the virtual environment active:

```powershell
python scraper\main.py
```

This contacts external websites and writes event, category, metadata, and lifecycle changes to the configured database. Failed, empty, or severely incomplete collections cannot deactivate existing events. Inactive records remain stored rather than being deleted.

`scraper/backfill_metadata.py` also contacts sources, including in preview mode. `scraper/backfill_categories.py` previews categories from stored rows. Both scripts accept `--apply` to write changes; they are maintenance tools, not tests.

Scraper HTTP sessions restrict requests and redirects to each source's HTTPS hostname and its `www` variant on the default HTTPS port. Off-source destinations and URLs containing credentials are rejected. If a source changes its domain or redirects elsewhere, review the change before adjusting the restriction.

## Tests and Checks

From the repository root, with the virtual environment active:

```powershell
Remove-Item Env:EVENT_ALERT_RUN_DB_TESTS -ErrorAction SilentlyContinue
python -m unittest discover -s scraper/tests
python -m pip check
Get-ChildItem api -Filter *.php -Recurse | ForEach-Object { php -l $_.FullName }
```

Offline unit tests cover normalization, categorization, source parsing, and HTTP destination restrictions using in-memory examples and mocked responses. They require no live scraping or database reset.

Six category synchronization tests are skipped unless `EVENT_ALERT_RUN_DB_TESTS=1` and the required database variables are set. They write inside rollback transactions and depend on specific existing event IDs and data. An empty schema is not enough to run them successfully. Use only a separate disposable database with suitable fixtures, never your working event database.

If Node.js is already installed, check JavaScript syntax with:

```powershell
node --check frontend/js/common.js
node --check frontend/js/app.js
node --check frontend/js/event.js
```

Node.js is an optional checking tool, not an application dependency. Syntax and unit checks do not establish production readiness or verify the current external source layouts.

## Sources and Known Limitations

The seven sources are Gemeente Gouda, Cultuurhuis Garenspinnerij, UitGouda, Volksuniversiteit Gouda, SPORT•GOUDA, Chocoladefabriek Gouda, and Gouda Bruist.

The nine categories are Community, Sport, Kids & Family, Culture, Workshop, Lecture, Market, Exhibition, and Other. Classification uses deterministic rules and can misclassify events. No AI extraction or classification is implemented.

Source page changes can break collection. Ambiguous dates, times, or locations may be omitted; missing metadata remains empty. The shared date normalizer currently defaults yearless dates to 2026. Duplicate detection uses title, start date, and city in application code rather than a database uniqueness constraint. The list API has no pagination.

## Sensitive Files and Source Data

Keep credentials, database dumps, collected records, logs, sessions, local configuration, and generated exports outside version control. `.gitignore` excludes common local artifacts; check `git status` and the staged diff before committing. Commit code, documentation, schema, migrations, category seeds, and small test examples.

External descriptions and media belong to their respective owners. Review each source's terms and permissions before collecting or redistributing content. Do not include source media or collected datasets in the repository. No open-source license has been selected for this project's code yet.
