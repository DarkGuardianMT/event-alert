import os
from contextlib import closing

import mysql.connector

from categorizer import CATEGORY_SLUGS, classify


def get_connection():
    required = (
        "EVENT_ALERT_DB_NAME",
        "EVENT_ALERT_DB_USER",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError("Ontbrekende omgevingsvariabelen: " + ", ".join(missing))

    return mysql.connector.connect(
        host=os.environ.get("EVENT_ALERT_DB_HOST", "localhost"),
        port=int(os.environ.get("EVENT_ALERT_DB_PORT", "3306")),
        database=os.environ["EVENT_ALERT_DB_NAME"],
        user=os.environ["EVENT_ALERT_DB_USER"],
        password=os.environ.get("EVENT_ALERT_DB_PASSWORD", ""),
        connection_timeout=10,
        autocommit=False,
    )


STORED_EVENT_FIELDS = (
    "title", "date_text", "start_date", "end_date", "start_time", "end_time", "description",
    "location", "city", "source", "source_url",
)


def load_category_ids(cursor):
    cursor.execute("SELECT id, slug FROM categories")
    category_ids = {slug: category_id for category_id, slug in cursor.fetchall()}
    if set(category_ids) != CATEGORY_SLUGS:
        raise ValueError("De categorieën in de database komen niet overeen met de regels.")
    return category_ids


def sync_category_links(cursor, event_id, slugs, category_ids):
    if not slugs or not slugs <= category_ids.keys():
        raise ValueError("Een evenement heeft ongeldige categorieën.")
    desired = {category_ids[slug] for slug in slugs}
    cursor.execute(
        "SELECT category_id FROM event_categories WHERE event_id = %s FOR UPDATE",
        (event_id,),
    )
    existing = {row[0] for row in cursor.fetchall()}
    for category_id in sorted(desired - existing):
        cursor.execute(
            "INSERT INTO event_categories (event_id, category_id) VALUES (%s, %s)",
            (event_id, category_id),
        )
    for category_id in sorted(existing - desired):
        cursor.execute(
            "DELETE FROM event_categories WHERE event_id = %s AND category_id = %s",
            (event_id, category_id),
        )


def load_stored_event(cursor, event_id):
    cursor.execute(
        "SELECT title, date_text, start_date, end_date, start_time, end_time, description, "
        "location, city, source, source_url "
        "FROM events WHERE id = %s FOR UPDATE",
        (event_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError("Het opgeslagen evenement ontbreekt.")
    return dict(zip(STORED_EVENT_FIELDS, row))


def sync_events(source_events, connection=None, deactivate=True):
    result = {
        "inserted": 0, "skipped": 0, "refreshed": 0, "deactivated": 0,
        "zero_sources": [], "low_coverage_sources": [],
    }
    duplicate_query = """
        SELECT id, source FROM events
        WHERE title = %s AND start_date <=> %s AND city <=> %s
        LIMIT 1 FOR UPDATE
    """
    insert_query = """
        INSERT INTO events
            (title, date_text, start_date, end_date, start_time, end_time, description,
             location, city, source, source_url, is_active, last_seen_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP(6))
    """
    refresh_query = """
        UPDATE events SET last_seen_at = CURRENT_TIMESTAMP(6), is_active = 1
        WHERE id = %s
    """
    metadata_query = """
        UPDATE events SET
            start_time = COALESCE(start_time, %s),
            end_time = COALESCE(end_time, %s),
            description = COALESCE(NULLIF(description, ''), %s)
        WHERE id = %s
    """
    own_connection = connection is None
    if own_connection:
        connection = get_connection()
    seen_ids = {source: set() for source in source_events}

    try:
        with closing(connection.cursor()) as cursor:
            category_ids = load_category_ids(cursor)
            for source, events in source_events.items():
                for event in events:
                    if event["source"] != source:
                        raise ValueError(f"Verkeerde bronnaam in evenement: {source}")
                    value = (
                        event["title"], event["date_text"],
                        # MySQL DATE-kolommen gebruiken NULL voor ontbrekende datums.
                        event["start_date"] or None, event["end_date"] or None,
                        event.get("start_time") or None, event.get("end_time") or None,
                        event.get("description") or None,
                        event["location"], event["city"], source, event["source_url"],
                    )
                    # De productie-identiteit blijft titel, startdatum en stad.
                    cursor.execute(duplicate_query, (value[0], value[2], value[8]))
                    existing = cursor.fetchone()
                    if existing is not None:
                        cursor.execute(refresh_query, (existing[0],))
                        if existing[1] == source:
                            cursor.execute(metadata_query, (value[4], value[5], value[6], existing[0]))
                        stored = load_stored_event(cursor, existing[0])
                        sync_category_links(cursor, existing[0], classify(stored), category_ids)
                        result["skipped"] += 1
                        result["refreshed"] += 1
                        if existing[1] == source:
                            seen_ids[source].add(existing[0])
                        continue
                    cursor.execute(insert_query, value)
                    result["inserted"] += cursor.rowcount
                    event_id = cursor.lastrowid
                    stored = load_stored_event(cursor, event_id)
                    sync_category_links(cursor, event_id, classify(stored), category_ids)
                    seen_ids[source].add(event_id)

            if deactivate:
                for source, events in source_events.items():
                    if not events:
                        # Een onverwacht lege bron kan een kapotte scraper betekenen.
                        result["zero_sources"].append(source)
                        continue
                    cursor.execute(
                        "SELECT COUNT(*) FROM events WHERE source = %s AND is_active = 1",
                        (source,),
                    )
                    active_count = cursor.fetchone()[0]
                    seen = seen_ids[source]
                    if active_count and len(seen) * 2 < active_count:
                        # Een grote daling is mogelijk een gedeeltelijke bronrespons.
                        result["low_coverage_sources"].append(source)
                        continue
                    if not seen:
                        continue
                    placeholders = ", ".join("%s" for _ in seen)
                    cursor.execute(
                        "UPDATE events SET is_active = 0 "
                        "WHERE source = %s AND is_active = 1 "
                        f"AND id NOT IN ({placeholders})",
                        (source, *sorted(seen)),
                    )
                    result["deactivated"] += cursor.rowcount
        if own_connection:
            connection.commit()
    except Exception:
        if own_connection:
            connection.rollback()
        raise
    finally:
        if own_connection:
            connection.close()
    return result


def insert_events(events):
    # Losse aanroepen vernieuwen bestaande rijen, maar sluiten geen bron af.
    if not events:
        return {"inserted": 0, "skipped": 0}
    grouped = {}
    for event in events:
        grouped.setdefault(event["source"], []).append(event)
    result = sync_events(grouped, deactivate=False)
    return {"inserted": result["inserted"], "skipped": result["skipped"]}


def backfill_event_metadata(source_events, connection=None, apply=False):
    result = {
        "matched": 0,
        "rows_updated": 0,
        "start_times_added": 0,
        "end_times_added": 0,
        "descriptions_added": 0,
    }
    own_connection = connection is None
    if own_connection:
        connection = get_connection()

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            for source, events in source_events.items():
                for event in events:
                    cursor.execute(
                        "SELECT id, start_time, end_time, description FROM events "
                        "WHERE title = %s AND start_date <=> %s AND city <=> %s AND source = %s "
                        "LIMIT 1 FOR UPDATE",
                        (event["title"], event["start_date"] or None, event["city"], source),
                    )
                    stored = cursor.fetchone()
                    if stored is None:
                        continue
                    result["matched"] += 1
                    additions = {
                        "start_time": event.get("start_time") if not stored["start_time"] else None,
                        "end_time": event.get("end_time") if not stored["end_time"] else None,
                        "description": event.get("description") if not stored["description"] else None,
                    }
                    if additions["start_time"]:
                        result["start_times_added"] += 1
                    if additions["end_time"]:
                        result["end_times_added"] += 1
                    if additions["description"]:
                        result["descriptions_added"] += 1
                    if not any(additions.values()):
                        continue
                    result["rows_updated"] += 1
                    if apply:
                        cursor.execute(
                            "UPDATE events SET start_time = COALESCE(start_time, %s), "
                            "end_time = COALESCE(end_time, %s), "
                            "description = COALESCE(NULLIF(description, ''), %s) WHERE id = %s",
                            (additions["start_time"], additions["end_time"],
                             additions["description"], stored["id"]),
                        )
        if own_connection:
            if apply:
                connection.commit()
            else:
                connection.rollback()
    except Exception:
        if own_connection:
            connection.rollback()
        raise
    finally:
        if own_connection:
            connection.close()
    return result
