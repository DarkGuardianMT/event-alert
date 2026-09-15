<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    header('Allow: GET');
    http_response_code(405);
    echo json_encode(['success' => false, 'event' => null, 'error' => 'Method not allowed.']);
    exit;
}

$rawId = $_GET['id'] ?? null;
$id = is_string($rawId) && preg_match('/\A[1-9][0-9]*\z/', $rawId)
    ? filter_var($rawId, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1, 'max_range' => 2147483647]])
    : false;

if ($id === false) {
    http_response_code(400);
    echo json_encode(['success' => false, 'event' => null, 'error' => 'Invalid event id.']);
    exit;
}

try {
    require_once __DIR__ . '/../config/database.php';

    $database = eventAlertDatabase();
    $statement = $database->prepare(
        'SELECT id, title, date_text, start_date, end_date, location, city, source, source_url '
        . 'FROM events WHERE id = :id AND is_active = 1'
    );
    $statement->bindValue(':id', $id, PDO::PARAM_INT);
    $statement->execute();
    $event = $statement->fetch();

    if ($event === false) {
        http_response_code(404);
        echo json_encode(['success' => false, 'event' => null, 'error' => 'Event not found.']);
        exit;
    }

    http_response_code(200);
    echo json_encode(['success' => true, 'event' => $event], JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
} catch (Throwable $error) {
    http_response_code(500);
    echo json_encode(['success' => false, 'event' => null, 'error' => 'Event is temporarily unavailable.']);
}
