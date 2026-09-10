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


def insert_events(events):
    if not events:
        return 0

    query = """
        INSERT INTO events
            (title, date_text, start_date, end_date, location, city, source, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = [
        (
            event["title"],
            event["date_text"],
            # MySQL DATE-kolommen gebruiken NULL voor ontbrekende datums.
            event["start_date"] or None,
            event["end_date"] or None,
            event["location"],
            event["city"],
            event["source"],
            event["source_url"],
        )
        for event in events
    ]

    with closing(get_connection()) as connection:
        try:
            with closing(connection.cursor()) as cursor:
                cursor.executemany(query, values)
                inserted = cursor.rowcount
            connection.commit()
        except mysql.connector.Error:
            connection.rollback()
            raise

    return inserted
