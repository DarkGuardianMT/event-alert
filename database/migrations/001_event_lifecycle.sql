-- Controleer de bestaande kolommen voordat deze eenmalige migratie wordt uitgevoerd.
ALTER TABLE events
    ADD COLUMN last_seen_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) AFTER source_url,
    ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER last_seen_at;
