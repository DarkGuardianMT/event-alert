ALTER TABLE events
    ADD COLUMN start_time TIME NULL AFTER end_date,
    ADD COLUMN end_time TIME NULL AFTER start_time,
    ADD COLUMN description TEXT NULL AFTER end_time;
