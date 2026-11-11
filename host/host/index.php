<?php
require __DIR__ . '/auth.php';
require_login();

$config = require '/var/www/private/config.php';

function h($value): string
{
    return htmlspecialchars((string)$value, ENT_QUOTES, 'UTF-8');
}

$error = '';
$devices = [];
$events = [];
$now = '';

try {
    $dsn = "mysql:host={$config['db_host']};dbname={$config['db_name']};charset=utf8mb4";
    $pdo = new PDO($dsn, $config['db_user'], $config['db_pass'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);

    $now = $pdo->query('SELECT NOW()')->fetchColumn();

    $devices = $pdo->query(
        'SELECT device_name,
                COUNT(*) AS total,
                SUM(is_reverse) AS reverse_count,
                MAX(occurred_at) AS last_at
         FROM events
         GROUP BY device_name
         ORDER BY device_name'
    )->fetchAll();

    $events = $pdo->query(
        'SELECT id, device_name, occurred_at, received_at, track_id, direction, is_reverse
         FROM events
         ORDER BY id DESC
         LIMIT 50'
    )->fetchAll();

    $totalEvents = array_sum(array_column($devices, 'total'));
    $totalReverse = array_sum(array_column($devices, 'reverse_count'));
    $reverseRate = $totalEvents > 0 ? ($totalReverse / $totalEvents) * 100 : 0;
} catch (PDOException $e) {
    error_log('safestep dashboard failed: ' . $e->getMessage());
    $error = 'データを取得できませんでした。';
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>SafeStep ダッシュボード</title>
<link rel="stylesheet" href="assets/dashboard.css">
</head>
<body>
<main class="shell">
<header class="topbar">
    <div>
<h1>SafeStep AI ダッシュボード</h1>
<p class="meta">
    サーバー時刻: <?= h($now) ?>（5秒ごとに自動更新）
</p>
    </div>
    <a href="logout.php">ログアウト</a>
</header>

<?php if ($error !== ''): ?>
<p class="error" role="alert"><?= h($error) ?></p>
<?php else: ?>

<section class="metrics" aria-label="全体の状況">
    <div class="metric">
        <span class="metric-label">イベント総数</span>
        <strong class="metric-value"><?= number_format($totalEvents) ?></strong>
        <div class="metric-note">全端末の累計</div>
    </div>
    <div class="metric alert">
        <span class="metric-label">逆走件数</span>
        <strong class="metric-value"><?= number_format($totalReverse) ?></strong>
        <div class="metric-note">全端末の累計</div>
    </div>
    <div class="metric alert">
        <span class="metric-label">逆走率</span>
        <strong class="metric-value"><?= number_format($reverseRate, 1) ?>%</strong>
        <div class="metric-note">逆走件数 ÷ イベント総数</div>
    </div>
</section>

<section>
<div class="section-head">
    <h2>イベント分析</h2>
    <span class="section-note">直近24時間・時間別集計</span>
</div>
<p class="chart-status" id="chart-status" role="status">グラフデータを読み込んでいます。</p>
<div class="charts">
    <div class="chart-panel">
        <h3>時間別イベント・逆走率</h3>
        <div class="chart-wrap"><canvas id="hourly-chart" aria-label="時間別イベントと逆走率"></canvas></div>
    </div>
    <div class="chart-panel chart-panel-doughnut">
        <h3>通常・逆走の割合</h3>
        <div class="chart-wrap"><canvas id="direction-chart" aria-label="通常イベントと逆走イベントの割合"></canvas></div>
    </div>
</div>
</section>

<section>
<div class="section-head">
    <h2>端末ごとの状況</h2>
    <span class="section-note">バーは各端末の逆走率</span>
</div>
<div class="panel scroll">
<table>
    <thead><tr>
        <th>端末</th>
        <th>イベント件数</th>
        <th>逆走件数</th>
        <th>逆走率</th>
        <th>最後のイベント</th>
    </tr></thead>
    <tbody>
    <?php if (count($devices) === 0): ?>
    <tr><td class="empty" colspan="5">まだイベントがありません。</td></tr>
    <?php endif; ?>
    <?php foreach ($devices as $d): ?>
    <?php $deviceRate = ((int)$d['reverse_count'] / (int)$d['total']) * 100; ?>
    <tr>
        <td><?= h($d['device_name']) ?></td>
        <td><?= number_format((int)$d['total']) ?></td>
        <td><?= number_format((int)$d['reverse_count']) ?></td>
        <td class="rate-cell">
            <div class="rate-line">
                <span class="rate-value"><?= number_format($deviceRate, 1) ?>%</span>
                <progress class="rate-meter<?= $deviceRate > 0 ? ' alert' : '' ?>" value="<?= min(100, $deviceRate) ?>" max="100" aria-label="逆走率 <?= number_format($deviceRate, 1) ?>%">
                    <?= number_format($deviceRate, 1) ?>%
                </progress>
            </div>
        </td>
        <td><?= h($d['last_at']) ?></td>
    </tr>
    <?php endforeach; ?>
    </tbody>
</table>
</div>
</section>

<section>
<div class="section-head">
    <h2>最新のイベント</h2>
    <span class="section-note">最大50件</span>
</div>
<div class="panel scroll">
<table>
    <thead><tr>
        <th>ID</th>
        <th>端末</th>
        <th>検出時刻</th>
        <th>受信時刻</th>
        <th>Track ID</th>
        <th>画面上の方向</th>
        <th>判定</th>
    </tr></thead>
    <tbody>
    <?php if (count($events) === 0): ?>
    <tr><td class="empty" colspan="7">まだイベントがありません。</td></tr>
    <?php endif; ?>
    <?php foreach ($events as $e): ?>
    <tr<?= $e['is_reverse'] ? ' class="reverse"' : '' ?>>
        <td><?= (int)$e['id'] ?></td>
        <td><?= h($e['device_name']) ?></td>
        <td><?= h($e['occurred_at']) ?></td>
        <td><?= h($e['received_at']) ?></td>
        <td><?= (int)$e['track_id'] ?></td>
        <td><?= $e['direction'] === 'UP' ? '↑ UP' : '↓ DOWN' ?></td>
        <td><span class="badge"><?= $e['is_reverse'] ? '逆走' : '通常' ?></span></td>
    </tr>
    <?php endforeach; ?>
    </tbody>
</table>
</div>
</section>

<?php endif; ?>
</main>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js" defer></script>
<script src="assets/dashboard.js" defer></script>
</body>
</html>