<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    header('Allow: GET');
    http_response_code(405);
    echo json_encode(['success' => false, 'count' => 0, 'events' => [], 'error' => 'Method not allowed.']);
    exit;
}

function invalidFilters(): void
{
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'count' => 0,
        'events' => [],
        'error' => 'Invalid filters.',
    ]);
    exit;
}

function validDateFilter($value): bool
{
    if (!is_string($value) || !preg_match('/\A[0-9]{4}-[0-9]{2}-[0-9]{2}\z/', $value)) {
        return false;
    }

    return checkdate(
        (int) substr($value, 5, 2),
        (int) substr($value, 8, 2),
        (int) substr($value, 0, 4)
    );
}

$filters = [];
foreach (['from', 'to'] as $name) {
    if (array_key_exists($name, $_GET)) {
        if (!validDateFilter($_GET[$name])) {
            invalidFilters();
        }
        $filters[$name] = $_GET[$name];
    }
}

if (isset($filters['from'], $filters['to']) && strcmp($filters['from'], $filters['to']) > 0) {
    invalidFilters();
}

if (array_key_exists('city', $_GET)) {
    if (!is_string($_GET['city'])) {
        invalidFilters();
    }
    $filters['city'] = $_GET['city'];
}

if (array_key_exists('category', $_GET)) {
    if (!is_string($_GET['category'])) {
        invalidFilters();
    }
    $filters['category'] = $_GET['category'];
}

try {
    require_once __DIR__ . '/../config/database.php';
    require_once __DIR__ . '/../config/categories.php';

    $database = eventAlertDatabase();
    if (isset($filters['category']) && !eventAlertCategoryExists($database, $filters['category'])) {
        http_response_code(400);
        echo json_encode([
            'success' => false,
            'count' => 0,
            'events' => [],
            'error' => 'Invalid category',
        ]);
        exit;
    }

    $query =
        'SELECT id, title, date_text, start_date, end_date, start_time, end_time, '
        . 'location, city, source, source_url '
        . 'FROM events WHERE is_active = 1';
    $parameters = [];

    if (isset($filters['city'])) {
        $query .= ' AND BINARY city = BINARY :city';
        $parameters['city'] = $filters['city'];
    }
    if (isset($filters['from'])) {
        $query .= ' AND start_date >= :from_date';
        $parameters['from_date'] = $filters['from'];
    }
    if (isset($filters['to'])) {
        $query .= ' AND start_date <= :to_date';
        $parameters['to_date'] = $filters['to'];
    }
    if (isset($filters['category'])) {
        $query .= ' AND EXISTS ('
            . 'SELECT 1 FROM event_categories ec '
            . 'INNER JOIN categories c ON c.id = ec.category_id '
            . 'WHERE ec.event_id = events.id AND BINARY c.slug = BINARY :category'
            . ')';
        $parameters['category'] = $filters['category'];
    }

    $query .= ' ORDER BY start_date ASC, title ASC';
    $statement = $database->prepare($query);
    $statement->execute($parameters);
    $events = $statement->fetchAll();
    $eventIds = array_map(static fn(array $event): int => (int) $event['id'], $events);
    $categoriesByEvent = eventAlertCategoriesByEvent($database, $eventIds);
    foreach ($events as &$event) {
        $event['categories'] = $categoriesByEvent[(int) $event['id']] ?? [];
    }
    unset($event);

    http_response_code(200);
    echo json_encode([
        'success' => true,
        'count' => count($events),
        'events' => $events,
    ], JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
} catch (Throwable $error) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'count' => 0,
        'events' => [],
        'error' => 'Events are temporarily unavailable.',
    ]);
}
