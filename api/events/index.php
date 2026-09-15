<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    header('Allow: GET');
    http_response_code(405);
    echo json_encode(['success' => false, 'count' => 0, 'events' => [], 'error' => 'Method not allowed.']);
    exit;
}

try {
    require_once __DIR__ . '/../config/database.php';

    $database = eventAlertDatabase();
    $statement = $database->query(
        'SELECT id, title, date_text, start_date, end_date, location, city, source, source_url '
        . 'FROM events WHERE is_active = 1 ORDER BY start_date ASC, title ASC'
    );
    $events = $statement->fetchAll();

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
