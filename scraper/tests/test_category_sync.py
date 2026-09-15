import os
import unittest
from contextlib import closing
from unittest.mock import patch

import database


@unittest.skipUnless(
    os.environ.get("EVENT_ALERT_DB_NAME") and os.environ.get("EVENT_ALERT_DB_USER"),
    "Een lokale Event Alert-testdatabase is vereist.",
)
class CategorySyncTests(unittest.TestCase):
    def stored(self, event_id, connection=None):
        own = connection is None
        if own:
            connection = database.get_connection()
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(
                    "SELECT id, title, date_text, start_date, end_date, location, city, "
                    "source, source_url, is_active, last_seen_at FROM events WHERE id = %s",
                    (event_id,),
                )
                event = cursor.fetchone()
                cursor.execute(
                    "SELECT c.slug FROM event_categories ec "
                    "JOIN categories c ON c.id = ec.category_id "
                    "WHERE ec.event_id = %s ORDER BY c.slug",
                    (event_id,),
                )
                categories = tuple(row["slug"] for row in cursor.fetchall())
            return event, categories
        finally:
            if own:
                connection.close()

    @staticmethod
    def incoming(stored):
        return {
            key: stored[key] for key in (
                "title", "date_text", "start_date", "end_date",
                "location", "city", "source", "source_url",
            )
        }

    def test_cross_source_duplicate_uses_stored_row(self):
        connection = database.get_connection()
        try:
            stored, original_categories = self.stored(270, connection)
            self.assertEqual(original_categories, ("workshop",))
            incoming = self.incoming(stored)
            incoming["source"] = "UitGouda"
            incoming["location"] = "Museum Gouda"
            result = database.sync_events({"UitGouda": [incoming]}, connection, deactivate=False)
            after, categories = self.stored(270, connection)
            self.assertEqual(result["skipped"], 1)
            self.assertEqual(result["inserted"], 0)
            self.assertEqual(after["source"], "Volksuniversiteit Gouda")
            self.assertEqual(categories, original_categories)
        finally:
            # Testwaarnemingen veranderen de echte levenscyclus niet.
            connection.rollback()
            connection.close()

    def test_inactive_duplicate_reactivates_inside_rollback(self):
        connection = database.get_connection()
        try:
            stored, original_categories = self.stored(47, connection)
            self.assertEqual(stored["is_active"], 0)
            result = database.sync_events(
                {stored["source"]: [self.incoming(stored)]}, connection, deactivate=False
            )
            after, categories = self.stored(47, connection)
            self.assertEqual(result["skipped"], 1)
            self.assertEqual(after["is_active"], 1)
            self.assertNotEqual(after["last_seen_at"], stored["last_seen_at"])
            self.assertEqual(categories, original_categories)
        finally:
            connection.rollback()
            connection.close()
        self.assertEqual(self.stored(47)[0]["is_active"], 0)

    def test_repeat_observations_do_not_duplicate_links(self):
        connection = database.get_connection()
        try:
            stored, original_categories = self.stored(304, connection)
            for _ in range(2):
                result = database.sync_events(
                    {stored["source"]: [self.incoming(stored)]}, connection, deactivate=False
                )
                self.assertEqual(result["skipped"], 1)
            self.assertEqual(self.stored(304, connection)[1], original_categories)
        finally:
            connection.rollback()
            connection.close()

    def test_new_event_gets_categories_inside_rollback(self):
        title = "Event Alert controlled buurtsport insertion check"
        incoming = {
            "title": title,
            "date_text": "31 december 2099",
            "start_date": "2099-12-31",
            "end_date": "2099-12-31",
            "location": "Testlocatie",
            "city": "Gouda",
            "source": "Gemeente Gouda",
            "source_url": "https://example.invalid/event",
        }
        connection = database.get_connection()
        try:
            result = database.sync_events(
                {"Gemeente Gouda": [incoming]}, connection, deactivate=False
            )
            self.assertEqual(result["inserted"], 1)
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT id FROM events WHERE title = %s", (title,))
                event_id = cursor.fetchone()[0]
            stored, categories = self.stored(event_id, connection)
            self.assertEqual(stored["is_active"], 1)
            self.assertEqual(categories, ("community", "sport"))
        finally:
            connection.rollback()
            connection.close()
        with closing(database.get_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT COUNT(*) FROM events WHERE title = %s", (title,))
                self.assertEqual(cursor.fetchone()[0], 0)

    def test_category_failure_rolls_back_refresh(self):
        stored, original_categories = self.stored(270)
        with patch.object(database, "sync_category_links", side_effect=RuntimeError("test failure")):
            with self.assertRaises(RuntimeError):
                database.sync_events(
                    {stored["source"]: [self.incoming(stored)]}, deactivate=False
                )
        after, categories = self.stored(270)
        self.assertEqual(after["last_seen_at"], stored["last_seen_at"])
        self.assertEqual(after["is_active"], stored["is_active"])
        self.assertEqual(categories, original_categories)


if __name__ == "__main__":
    unittest.main()
