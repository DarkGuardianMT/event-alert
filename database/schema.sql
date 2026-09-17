CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    date_text VARCHAR(255),
    start_date DATE,
    end_date DATE,
    start_time TIME NULL,
    end_time TIME NULL,
    description TEXT NULL,
    location VARCHAR(255),
    city VARCHAR(100),
    source VARCHAR(100),
    source_url TEXT,
    last_seen_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(40) NOT NULL,
    name_nl VARCHAR(80) NOT NULL,
    name_en VARCHAR(80) NOT NULL,
    sort_order SMALLINT UNSIGNED NOT NULL,
    UNIQUE KEY uq_categories_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE event_categories (
    event_id INT NOT NULL,
    category_id SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (event_id, category_id),
    KEY idx_category_event (category_id, event_id),
    CONSTRAINT fk_event_categories_event FOREIGN KEY (event_id)
        REFERENCES events(id) ON DELETE RESTRICT,
    CONSTRAINT fk_event_categories_category FOREIGN KEY (category_id)
        REFERENCES categories(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO categories (slug, name_nl, name_en, sort_order) VALUES
    ('community', 'Buurt & gemeenschap', 'Community', 1),
    ('sport', 'Sport', 'Sport', 2),
    ('kids_family', 'Kinderen & gezin', 'Kids & Family', 3),
    ('culture', 'Cultuur', 'Culture', 4),
    ('workshop', 'Workshop', 'Workshop', 5),
    ('lecture', 'Lezing', 'Lecture', 6),
    ('market', 'Markt', 'Market', 7),
    ('exhibition', 'Tentoonstelling', 'Exhibition', 8),
    ('other', 'Overig', 'Other', 9);
