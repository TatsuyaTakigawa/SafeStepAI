<?php
require __DIR__ . '/auth.php';

$config = require __DIR__ . '/../../../safestep_private/config.php';
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $user = $_POST['username'] ?? '';
    $pass = $_POST['password'] ?? '';

    if (
        hash_equals($config['username'], $user) &&
        password_verify($pass, $config['password_hash'])
    ) {
        session_regenerate_id(true);
        $_SESSION['logged_in'] = true;
        header('Location: index.php');
        exit;
    }

    sleep(1);
    $error = 'ユーザー名またはパスワードが違います。';
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SafeStep ログイン</title>
<link rel="stylesheet" href="assets/login.css">
</head>
<body class="login-page">
<main class="login-layout">
<section class="brand-panel" aria-label="SafeStep AI">
    <div class="brand-lockup">
        <span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span></span>
        <span class="brand-name">SafeStep<span class="brand-ai">AI</span></span>
    </div>
    <div class="brand-message">
        <p class="eyebrow">SAFETY MONITORING</p>
        <h1>SafeStep<br>管理画面</h1>
        <p class="brand-caption">SECURE ACCESS <span aria-hidden="true">/</span> 01</p>
    </div>
    <div class="lane-art" aria-hidden="true">
        <span class="lane-line lane-line-one"></span>
        <span class="lane-line lane-line-two"></span>
        <span class="lane-line lane-line-three"></span>
        <span class="lane-node lane-node-one"></span>
        <span class="lane-node lane-node-two"></span>
        <span class="lane-node lane-node-three"></span>
        <span class="lane-arrow">↑</span>
    </div>
    <span class="panel-index">SS / CONTROL</span>
</section>

<section class="form-panel">
    <div class="form-content">
        <p class="form-kicker">ACCOUNT ACCESS</p>
        <h2>ログイン</h2>
        <p class="form-intro">登録済みのアカウント情報を入力してください。</p>
<?php if ($error !== ''): ?>
        <p class="login-error" id="login-error" role="alert"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p>
<?php endif; ?>
        <form class="login-form" method="post">
            <div class="field">
                <label for="username">ユーザー名</label>
                <input id="username" type="text" name="username" autocomplete="username" required<?= $error !== '' ? ' aria-describedby="login-error"' : '' ?>>
            </div>
            <div class="field">
                <label for="password">パスワード</label>
                <input id="password" type="password" name="password" autocomplete="current-password" required>
            </div>
            <button type="submit">ログイン <span aria-hidden="true">→</span></button>
        </form>
        <p class="form-footnote"><span class="status-dot" aria-hidden="true"></span>保護された接続</p>
    </div>
</section>
</main>
</body>
</html>