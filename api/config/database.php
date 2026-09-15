<?php

declare(strict_types=1);

function eventAlertDatabase(): PDO
{
    $host = getenv('EVENT_ALERT_DB_HOST') ?: 'localhost';
    $port = getenv('EVENT_ALERT_DB_PORT') ?: '3306';
    $database = getenv('EVENT_ALERT_DB_NAME') ?: 'event_alert';
    $user = getenv('EVENT_ALERT_DB_USER') ?: 'root';
    $password = getenv('EVENT_ALERT_DB_PASSWORD');

    $dsn = "mysql:host={$host};port={$port};dbname={$database};charset=utf8mb4";

    return new PDO($dsn, $user, $password === false ? '' : $password, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
}
