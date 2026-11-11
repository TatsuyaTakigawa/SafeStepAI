<?php
require __DIR__ . '/../auth.php';
require_login();

header('Content-Type: application/json; charset=utf-8');

$config = require '/var/www/private/config.php';

try {
    $dsn = "mysql:host={$config['db_host']};dbname={$config['db_name']};charset=utf8mb4";
    $pdo = new PDO($dsn, $config['db_user'], $config['db_pass'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);

    $hours = $pdo->query(
        "SELECT DATE_FORMAT(occurred_at, '%Y-%m-%d %H:00') AS hour,
                COUNT(*) AS total,
                COALESCE(SUM(is_reverse), 0) AS reverse_count,
                COUNT(DISTINCT CONCAT(device_name, ':', track_id)) AS people_count
         FROM events
         WHERE occurred_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
         GROUP BY DATE_FORMAT(occurred_at, '%Y-%m-%d %H:00')
         ORDER BY hour"
    )->fetchAll();

    echo json_encode(['hours' => $hours], JSON_UNESCAPED_UNICODE);
} catch (PDOException $e) {
    error_log('safestep analytics failed: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'analytics unavailable'], JSON_UNESCAPED_UNICODE);
}