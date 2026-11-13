# データベース設計書

- 対象システム：SafeStep AI
- 文書の位置づけ：現行実装に基づくデータベース設計
- 更新日：2026年11月11日

## 1. 目的と適用範囲

本書は、現行のダッシュボード/APIが利用するイベントデータベースを定義します。検知端末は通過イベントをHTTP APIへ送信し、WebアプリケーションがMariaDBの`events`テーブルへ保存します。

本書は[`001-create-events.sql`](../host/database/init/001-create-events.sql)、[`event.php`](../host/host/api/event.php)、[`analytics.php`](../host/host/api/analytics.php)、[`index.php`](../host/host/index.php)の実装に合わせています。旧設計に記載されていたSQLiteの`detection_log`および`statistics`テーブルは現行実装では使用していません。

## 2. データ管理方針

- DBMSはMariaDB 11.4、ストレージエンジンはInnoDBです。
- 1レコードは、仮想ラインを通過した人物の方向判定イベント1件です。音声アラーム1回を表す専用テーブルではありません。
- 画像・映像データはイベントAPIの保存対象ではありません。
- 追跡IDは端末側のイベントを集計・表示するためイベントレコードに記録します。個人を識別するIDとして扱いません。
- 集計値（逆走数、端末別件数、時間別件数など）はイベントデータからクエリ時に算出し、別の統計テーブルには保存しません。

## 3. テーブル一覧

| テーブル | 用途 | 作成定義 |
| --- | --- | --- |
| `events` | 端末から受信した方向判定イベント | [`001-create-events.sql`](../host/database/init/001-create-events.sql) |

## 4. `events`テーブル

### 4.1 カラム定義

| カラム | 型 | NULL | 初期値 | 説明 |
| --- | --- | --- | --- | --- |
| `id` | `BIGINT UNSIGNED` | 不可 | 自動採番 | イベント主キー |
| `device_name` | `VARCHAR(64)` | 不可 | なし | 検知端末名。APIで英数字、`_`、`-`の1〜64文字に制限 |
| `occurred_at` | `DATETIME` | 不可 | なし | 検知端末が記録したイベント時刻 |
| `received_at` | `TIMESTAMP` | 不可 | `CURRENT_TIMESTAMP` | DBがイベントを受信・登録した時刻 |
| `track_id` | `BIGINT UNSIGNED` | 不可 | なし | 物体追跡器が付与した一時的な追跡ID |
| `direction` | `ENUM('UP','DOWN')` | 不可 | なし | 画面上の通過方向 |
| `is_reverse` | `TINYINT(1)` | 不可 | `0` | 通常方向なら`0`、設定方向と逆なら`1` |

### 4.2 主キーとインデックス

| 名称 | 対象 | 用途 |
| --- | --- | --- |
| `PRIMARY KEY` | `id` | レコードの一意識別 |
| `idx_events_occurred_at` | `occurred_at` | 時刻範囲の検索・集計 |
| `idx_events_device_occurred` | `device_name`, `occurred_at` | 端末別の時刻検索・集計 |
| `idx_events_reverse` | `is_reverse` | 逆走イベントの抽出 |

外部キーは定義していません。

### 4.3 DDL

```sql
CREATE TABLE IF NOT EXISTS events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    device_name VARCHAR(64) NOT NULL,
    occurred_at DATETIME NOT NULL,
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    track_id BIGINT UNSIGNED NOT NULL,
    direction ENUM('UP', 'DOWN') NOT NULL,
    is_reverse TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    INDEX idx_events_occurred_at (occurred_at),
    INDEX idx_events_device_occurred (device_name, occurred_at),
    INDEX idx_events_reverse (is_reverse)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## 5. 登録インターフェース

[`event.php`](../host/host/api/event.php)の`POST /api/event.php`は`X-API-Key`ヘッダーでAPIキーを検証し、JSONの入力を検証した後に`events`へ登録します。成功時はHTTP 201と`{"ok":true}`を返します。

| JSON項目 | 型・制約 | 保存先 |
| --- | --- | --- |
| `device_name` | 文字列、英数字・`_`・`-`、1〜64文字 | `device_name` |
| `occurred_at` | `YYYY-MM-DD HH:MM:SS`形式 | `occurred_at` |
| `track_id` | 0以上の整数 | `track_id` |
| `direction` | `UP`または`DOWN` | `direction` |
| `is_reverse` | `0`または`1`。省略時は`0` | `is_reverse` |

イベントAPIの通信に画像データは含まれません。DB側の`received_at`はDB登録時に設定されるため、クライアントから送信しません。

## 6. 集計と参照

- ダッシュボード（[`index.php`](../host/host/index.php)）は全イベント数、逆走イベント数、逆走率をイベントレコードから算出します。
- 端末別の集計は端末ごとのイベント数、逆走数、最終検知時刻を表示します。
- 最新イベントは`id`の降順で最大50件表示します。
- 分析API（[`analytics.php`](../host/host/api/analytics.php)）は直近24時間を時間単位で集計し、イベント数、逆走数、`device_name`と`track_id`の組み合わせによる人数カウントを返します。
- ダッシュボードと分析APIはログインセッションを要求します。

これらは表示時の集計であり、`statistics`等の集計テーブルへの定期保存を意味しません。

## 7. 運用上の注意

- Docker Composeの`db_data`ボリュームにDBデータを永続化します。`docker compose down -v`はボリュームを削除するため、通常の停止・再起動では使用しないでください。構成は[`compose.yaml`](../host/compose.yaml)を参照してください。
- 既存DBを移行する場合は、移行元のスキーマとデータを先にバックアップし、現行SQL定義およびPHPが参照する列との互換性を確認してください。
- APIキー、DBパスワード、ログイン情報はリポジトリに登録せず、環境設定・非公開設定ファイルで管理してください。
- 定期バックアップを実施し、実際に復元できることも確認してください。手順は[`host/README.md`](../host/README.md)を参照してください。

## 8. 参照実装

- [`001-create-events.sql`](../host/database/init/001-create-events.sql)
- [`event.php`](../host/host/api/event.php)
- [`analytics.php`](../host/host/api/analytics.php)
- [`index.php`](../host/host/index.php)
- [`compose.yaml`](../host/compose.yaml)
