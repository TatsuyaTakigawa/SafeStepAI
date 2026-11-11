# SafeStep AI - Docker Compose deployment

## 構成

- PHP 8.3 + Apache (`php:8.3-apache-bookworm`)
- MariaDB 11.4 (`mariadb:11.4`)
- Docker volume `db_data` にDBデータを永続化
- `restart: unless-stopped` で常時稼働を想定
- DBはCompose内部ネットワークのみ。ホスト側へ3306番を公開しません。
- PHP設定ファイルはWeb公開ディレクトリ外の `/var/www/private/config.php` に読み取り専用でマウントします。

## 重要：既存DBを先にバックアップ

このアーカイブには `host/` のWebアプリケーションのみが含まれ、元の `safestep_private/config.php` とMySQLデータベースのダンプは含まれていません。
そのため、元環境のDB接続情報・ログイン情報・APIキーは、元環境から安全に移してください。新規の認証情報を設定すると、既存クライアント側のAPIキー等も更新が必要になる場合があります。

元のMySQLで、まずバックアップを取得してください（DB名は実際の値に置き換えます）。

```bash
mysqldump -u <DB_USER> -p --single-transaction --routines --triggers <DB_NAME> > safestep-backup.sql
```

既存の `events` テーブル定義を必ず確認してください。`database/init/001-create-events.sql` は、添付PHPコードから読み取れる列をもとにした新規構築用の初期スキーマです。元DBに既存テーブルがある場合は、元DBのスキーマを優先してください。

## Raspberry Pi 5への配置

1. Raspberry Pi OS 64-bit (ARM64) を用意し、Docker Engine と Docker Compose plugin をインストールします。
2. このフォルダーをPiへコピーし、作業ディレクトリを `SafeStepAI-docker` にします。
3. `.env.example` を `.env` にコピーし、値を設定します。
4. `private/config.php` はコンテナ外・Web公開領域外に置きます（Composeが読み取り専用でマウントします）。
5. DBバックアップを移行する場合は、下記「既存DBの復元」を参照してからWebを起動します。

```bash
cp .env.example .env
mkdir -p logs/apache
```

`.env` の `DB_PASSWORD` と `DB_ROOT_PASSWORD` は別々の長いランダム値に変更してください。`.env` はGit等へコミットしないでください。

ログインパスワードのハッシュを生成する例：

```bash
docker run --rm php:8.3-cli php -r 'echo password_hash("ここにログインパスワード", PASSWORD_DEFAULT), PHP_EOL;'
```

出力されたハッシュを `.env` の `APP_PASSWORD_HASH` に設定します。bcrypt等のハッシュには `$` が含まれるため、`.env` では必ずシングルクォートで囲んでください（例：`APP_PASSWORD_HASH='$2y$...'`）。`APP_USERNAME` にはログインユーザー名を設定します。`API_KEY` はイベント送信元が送る `X-API-Key` と一致させます。

## private/config.php

`.env` の値をPHPから読み込む設定ファイルです。通常はそのまま利用できます。

```php
<?php
declare(strict_types=1);

return [
    'db_host' => getenv('DB_HOST') ?: 'db',
    'db_name' => getenv('DB_NAME') ?: 'safestep',
    'db_user' => getenv('DB_USER') ?: 'safestep',
    'db_pass' => getenv('DB_PASSWORD') ?: '',
    'username' => getenv('APP_USERNAME') ?: '',
    'password_hash' => getenv('APP_PASSWORD_HASH') ?: '',
    'api_key' => getenv('API_KEY') ?: '',
];
```

元システムの `safestep_private/config.php` にあるキー名は、PHP側で使用している `db_host`, `db_name`, `db_user`, `db_pass`, `username`, `password_hash`, `api_key` です。値を移行する際に取り違えないでください。

## 既存DBの復元

既存DBのフルダンプを使う場合、初期化SQLによる仮テーブル作成を避けるため、初回起動前に次のファイルを一時的に別の場所へ移動します。

```bash
mkdir -p database/init.disabled
mv database/init/001-create-events.sql database/init.disabled/
```

DBだけ起動します。

```bash
docker compose up -d db
docker compose ps
```

ダンプをインポートします（`safestep-backup.sql` をPi上に配置し、`.env` のDB名・ユーザー名に合わせてください）。

```bash
docker compose exec -T db sh -c 'exec mariadb -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE"' < safestep-backup.sql
```

インポート後、`events` の列・インデックス・文字コードが元環境と一致することを確認してください。元DBをフルダンプから復元した場合、初期化SQLを戻す必要はありません。初期化SQLは新規DB用です。

## 新規DBで起動する場合

既存DBを復元しない場合は、同梱の初期化SQLをそのまま使います。

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

ブラウザーで `http://<Raspberry-PiのIPアドレス>:8080/` を開きます。

## 動作確認

イベントAPI（APIキーは実際の値に置換）：

```bash
curl -i -X POST http://<Raspberry-PiのIPアドレス>:8080/api/event.php \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <API_KEY>' \
  -d '{"device_name":"device_01","occurred_at":"2026-11-06 10:00:00","track_id":1,"direction":"UP","is_reverse":0}'
```

成功時はHTTP 201と `{"ok":true}` が返ります。ダッシュボードと分析APIはログインセッションが必要です。

ログ確認：

```bash
docker compose logs --tail=100 web
docker compose logs --tail=100 db
```

停止・再起動：

```bash
docker compose down
docker compose up -d
```

`docker compose down -v` はDBボリュームも削除するため、通常運用では実行しないでください。

## バックアップ

定期的にDBダンプを取得し、Pi本体以外にもコピーしてください。

```bash
mkdir -p backups
docker compose exec -T db sh -c 'exec mariadb-dump -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE"' > "backups/safestep-$(date +%F).sql"
```

## 運用上の注意

- このComposeはHTTPの8080番で公開します。インターネットへ直接公開せず、LAN内またはVPN経由で利用してください。外部公開が必要ならTLS対応リバースプロキシ（Caddy等）を前段に追加し、ファイアウォールも設定してください。
- `dashboard.js` はChart.jsをjsDelivr CDNから読み込みます。管理画面を開く端末にインターネット接続がない場合は、Chart.jsをローカル配信へ切り替えてください。
- Raspberry Pi 5の冷却・電源・ストレージ品質を確保してください。24/7用途では高耐久microSDよりSSDの利用を推奨します。
- `restart: unless-stopped` はプロセス停止時の再起動設定であり、電源・ストレージ故障やDBバックアップの代替にはなりません。
- イメージタグはメジャー・マイナーバージョンを固定していますが、長期運用では定期的にセキュリティ更新とバックアップ検証を行ってください。
- 実機でのビルド・負荷・長期稼働テストは、この作成環境では実施していません。初回は必ずテストデータで動作確認してください。
