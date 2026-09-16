<?php

declare(strict_types=1);

function eventAlertCategoryExists(PDO $database, string $slug): bool
{
    $statement = $database->prepare(
        'SELECT 1 FROM categories WHERE BINARY slug = BINARY :slug LIMIT 1'
    );
    $statement->execute(['slug' => $slug]);

    return $statement->fetchColumn() !== false;
}

function eventAlertCategoriesByEvent(PDO $database, array $eventIds): array
{
    if ($eventIds === []) {
        return [];
    }

    $categoriesByEvent = array_fill_keys($eventIds, []);
    $placeholders = implode(', ', array_fill(0, count($eventIds), '?'));
    $statement = $database->prepare(
        'SELECT ec.event_id, c.slug, c.name_nl, c.name_en '
        . 'FROM event_categories ec '
        . 'INNER JOIN categories c ON c.id = ec.category_id '
        . "WHERE ec.event_id IN ({$placeholders}) "
        . 'ORDER BY ec.event_id ASC, c.sort_order ASC, c.id ASC'
    );
    $statement->execute($eventIds);

    foreach ($statement->fetchAll() as $category) {
        $eventId = (int) $category['event_id'];
        unset($category['event_id']);
        $categoriesByEvent[$eventId][] = $category;
    }

    return $categoriesByEvent;
}
