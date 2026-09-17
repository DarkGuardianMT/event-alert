"""Toon categorieën vooraf of vul ze transactioneel aan voor opgeslagen evenementen."""

import argparse
from collections import Counter
from contextlib import closing
from itertools import islice

from categorizer import classify
from database import get_connection, load_category_ids, sync_category_links


EXAMPLE_TITLES = (
    "Buurtsport 12+ voor meiden", "Kinderboekencafé", "Historische Leesclub",
    "Expositie: Kunstgeluk", "Open Monumentendag", "Taalcafé",
    "Yoga tussen de schuttersstukken", "Snijtechnieken",
    "Lezing | Leendert van der Valk", "Wijkfeest Gouda Noord",
)


def stored_events(connection):
    with closing(connection.cursor(dictionary=True)) as cursor:
        cursor.execute(
            "SELECT id, title, date_text, start_date, end_date, description, location, city, "
            "source, source_url, is_active FROM events ORDER BY id"
        )
        return cursor.fetchall()


def event_counts(connection):
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT COUNT(*), SUM(is_active = 1), SUM(is_active = 0) FROM events"
        )
        return tuple(value or 0 for value in cursor.fetchone())


def preview(events):
    assignments = [(event, classify(event)) for event in events]
    distribution = Counter(slug for _, slugs in assignments for slug in slugs)
    multi_count = sum(len(slugs) > 1 for _, slugs in assignments)
    other = [(event, slugs) for event, slugs in assignments if slugs == {"other"}]
    other_by_source = Counter(event["source"] for event, _ in other)
    print(f"Evenementen in voorbeeld: {len(events)}")
    print(f"Meerdere categorieën: {multi_count}")
    print(f"Overig: {len(other)} ({len(other) / len(events):.1%})" if events else "Overig: 0")
    for slug in sorted(distribution):
        print(f"  {slug}: {distribution[slug]}")
    print("Overig per bron:")
    for source, count in other_by_source.most_common():
        print(f"  {source}: {count}")
    print("Voorbeelden:")
    for title in EXAMPLE_TITLES:
        match = next(
            ((event, slugs) for event, slugs in assignments
             if title.casefold() in event["title"].casefold()),
            None,
        )
        if match:
            event, slugs = match
            print(f"  {event['id']} {'actief' if event['is_active'] else 'inactief'} "
                  f"{event['title']}: {', '.join(sorted(slugs))}")
    print("Mogelijk onduidelijk (Overig, eerste 12):")
    for event, _ in other[:12]:
        print(f"  {event['id']} {event['source']}: {event['title']}")
    print("Grote overlap (meer dan drie categorieën, eerste 8):")
    for event, slugs in islice((item for item in assignments if len(item[1]) > 3), 8):
        print(f"  {event['id']} {event['title']}: {', '.join(sorted(slugs))}")
    return assignments


def apply(connection, assignments):
    before = event_counts(connection)
    try:
        with closing(connection.cursor()) as cursor:
            category_ids = load_category_ids(cursor)
            for event, slugs in assignments:
                sync_category_links(cursor, event["id"], slugs, category_ids)
            cursor.execute(
                "SELECT COUNT(*) FROM events e WHERE NOT EXISTS "
                "(SELECT 1 FROM event_categories ec WHERE ec.event_id = e.id)"
            )
            missing = cursor.fetchone()[0]
        after = event_counts(connection)
        if missing or before != after:
            raise ValueError("De categorie-dekking of levenscyclus is veranderd.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    print(f"Categorieën opgeslagen; evenementen voor/na: {before} / {after}")


def main():
    parser = argparse.ArgumentParser(description="Voorbeeld of backfill van evenementcategorieën")
    parser.add_argument("--apply", action="store_true", help="Schrijf categorie-koppelingen")
    args = parser.parse_args()
    connection = get_connection()
    try:
        events = stored_events(connection)
        assignments = preview(events)
        if args.apply:
            apply(connection, assignments)
        else:
            print("Alleen lezen; geen categorieën geschreven.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
