<?php
header('Content-Type: application/json; charset=utf-8');

function respond(int $status, array $body): void
{
    http_response_code($status);
    echo json_encode($body, JSON_UNESCAPED_UNICODE);
    exit;
}

// POST以外は受け付けない
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Allow: POST');
    respond(405, ['ok' => false, 'error' => 'method not allowed']);
}

$config = require __DIR__ . '/../../../safestep_private/config.php';

// APIキーの確認
$sent_key = $_SERVER['HTTP_X_API_KEY'] ?? '';
if (!is_string($sent_key) || $sent_key === '' || !hash_equals($config['api_key'], $sent_key)) {
    usleep(500000);
    respond(401, ['ok' => false, 'error' => 'unauthorized']);
}

// 本文(JSON)の読み取り(最大4096バイト)
$raw = file_get_contents('php://input', false, null, 0, 4096);
$data = json_decode($raw, true);
if (!is_array($data)) {
    respond(400, ['ok' => false, 'error' => 'invalid json']);
}

// device_name: 英数字・_・- のみ、1〜64文字
$device = $data['device_name'] ?? '';
if (!is_string($device) || !preg_match('/^[A-Za-z0-9_-]{1,64}$/', $device)) {
    respond(400, ['ok' => false, 'error' => 'invalid device_name']);
}

// occurred_at: "YYYY-MM-DD HH:MM:SS" の形式
$occurred = $data['occurred_at'] ?? '';
$dt = is_string($occurred) ? DateTime::createFromFormat('Y-m-d H:i:s', $occurred) : false;
if (!$dt || $dt->format('Y-m-d H:i:s') !== $occurred) {
    respond(400, ['ok' => false, 'error' => 'invalid occurred_at']);
}

// track_id: 0以上の整数
$track_id = $data['track_id'] ?? null;
if (!is_int($track_id) || $track_id < 0) {
    respond(400, ['ok' => false, 'error' => 'invalid track_id']);
}

// direction: UP または DOWN
$direction = $data['direction'] ?? '';
if ($direction !== 'UP' && $direction !== 'DOWN') {
    respond(400, ['ok' => false, 'error' => 'invalid direction']);
}

// is_reverse: 0 または 1(省略時は0)
$is_reverse = $data['is_reverse'] ?? 0;
if ($is_reverse !== 0 && $is_reverse !== 1) {
    respond(400, ['ok' => false, 'error' => 'invalid is_reverse']);
}

// DBへ保存
try {
    $dsn = "mysql:host={$config['db_host']};dbname={$config['db_name']};charset=utf8mb4";
    $pdo = new PDO($dsn, $config['db_user'], $config['db_pass'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);

    $stmt = $pdo->prepare(
        'INSERT INTO events (device_name, occurred_at, track_id, direction, is_reverse)
         VALUES (:device_name, :occurred_at, :track_id, :direction, :is_reverse)'
    );
    $stmt->execute([
        ':device_name' => $device,
        ':occurred_at' => $occurred,
        ':track_id'    => $track_id,
        ':direction'   => $direction,
        ':is_reverse'  => $is_reverse,
    ]);
} catch (PDOException $e) {
    error_log('safestep insert failed: ' . $e->getMessage());
    respond(500, ['ok' => false, 'error' => 'server error']);
}

respond(201, ['ok' => true]);