import os
from contextlib import closing

import mysql.connector


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
            (title, date_text, start_date, end_date, location, city, source, source_url,
             is_active, last_seen_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP(6))
    """
    refresh_query = """
        UPDATE events SET last_seen_at = CURRENT_TIMESTAMP(6), is_active = 1
        WHERE id = %s
    """
    own_connection = connection is None
    if own_connection:
        connection = get_connection()
    seen_ids = {source: set() for source in source_events}

    try:
        with closing(connection.cursor()) as cursor:
            for source, events in source_events.items():
                for event in events:
                    if event["source"] != source:
                        raise ValueError(f"Verkeerde bronnaam in evenement: {source}")
                    value = (
                        event["title"], event["date_text"],
                        # MySQL DATE-kolommen gebruiken NULL voor ontbrekende datums.
                        event["start_date"] or None, event["end_date"] or None,
                        event["location"], event["city"], source, event["source_url"],
                    )
                    # De productie-identiteit blijft titel, startdatum en stad.
                    cursor.execute(duplicate_query, (value[0], value[2], value[5]))
                    existing = cursor.fetchone()
                    if existing is not None:
                        cursor.execute(refresh_query, (existing[0],))
                        result["skipped"] += 1
                        result["refreshed"] += 1
                        if existing[1] == source:
                            seen_ids[source].add(existing[0])
                        continue
                    cursor.execute(insert_query, value)
                    result["inserted"] += cursor.rowcount
                    seen_ids[source].add(cursor.lastrowid)

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
