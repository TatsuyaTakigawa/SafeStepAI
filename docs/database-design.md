文書番号：SW106　SafeStep AI データベース設計書

文書番号　SW106

**データベース設計書**

**SafeStep**** AI**

学校階段 逆走検知・音声警告システム

| **承認** | **確認** | **作成** |
| --- | --- | --- |
|  |  | 滝川 達也 |

発行部署：SafeStep AI プロジェクトチーム

発行日：2026年8月7日

*本書は SW105「**SafeStep** AI ソフトウェア要求仕様書」4章の内容を独立した設計書として再構成したものである。*

改訂履歴

| **項番** | **日付** | **Ver** | **改訂内容** | **備考** |
| --- | --- | --- | --- | --- |
| 1 | 2026年9月9日 | 1.0 | 新規作成 |  |

1　概要

1.1　目的

本書は、SafeStep AI（学校階段逆走検知・音声警告システム）における、警告イベントおよび統計情報を管理するデータベースの設計内容を定義することを目的とする。

1.2　位置づけ

本書は、上位文書である SW105「SafeStep AI ソフトウェア要求仕様書」の記載内容に基づき、データベースの詳細設計を定めるものである。

1.3　管理方針

SafeStep AI では、逆走検知によって発生した警告イベントと、一定時間における統計情報を SQLite で管理する。

個人識別を目的としたデータや映像データは保存せず、統計・効果測定に必要な最小限の情報のみを保存する。

1.4　テーブル構成

- detection_log － 警告イベントを記録する（1レコード＝1回の警告イベント）

- statistics － 一定時間の集計結果を記録する（1レコード＝1回の統計集計）

2　detection_log テーブル

2.1　役割

音声警告が発生したイベントを記録する。

逆走を検知するたびに DB へ保存するのではなく、逆走カウントがしきい値に到達して音声警告が発生した時点で1レコードを保存する。

2.2　カラム定義

| **カラム名** | **データ型** | **NULL** | **DEFAULT** | **説明** |
| --- | --- | --- | --- | --- |
| id | INTEGER | 不可 | － | 警告イベントを一意に識別するID |
| detected_at | TEXT | 不可 | － | 警告が発生した日時 |
| reverse_count | INTEGER | 不可 | － | 警告発生時点で蓄積されていた逆走カウント |

2.3　制約

- PRIMARY KEY：id

- FOREIGN KEY：なし

- INDEX：追加なし

- AUTOINCREMENT：使用しない

2.4　日時形式

detected_at は以下の形式で保存する。

YYYY-MM-DD HH:MM:SS

例：2026-06-15 12:51:20

3　statistics テーブル

3.1　役割

一定時間における階段利用状況および逆走・警告の集計結果を記録する。

3.2　カラム定義

| **カラム名** | **データ型** | **NULL** | **DEFAULT** | **説明** |
| --- | --- | --- | --- | --- |
| id | INTEGER | 不可 | － | 統計情報を一意に識別するID |
| recorded_at | TEXT | 不可 | － | 統計情報を記録した日時 |
| total_users | INTEGER | 不可 | 0 | 仮想ラインを通過した総人数 |
| reverse_count | INTEGER | 不可 | 0 | 逆方向に仮想ラインを通過した回数 |
| warning_count | INTEGER | 不可 | 0 | 音声警告の発生回数 |

3.3　制約

- PRIMARY KEY：id

- FOREIGN KEY：なし

- INDEX：追加なし

- AUTOINCREMENT：使用しない

3.4　日時形式

recorded_at は以下の形式で保存する。

YYYY-MM-DD HH:MM:SS

例：2026-06-15 13:15:00

4　逆走カウントの考え方

逆走は、人物が仮想ラインをどちらから通過したかによって判定する。

4.1　通常方向に通過した場合

- total_users を1増加

- reverse_count は増加させない

4.2　逆方向に通過した場合

- total_users を1増加

- reverse_count を1増加

同一人物が何度も逆走するケースは想定しない。

また、フレーム単位で逆走判定を記録するのではなく、「仮想ラインを逆方向に通過した」というイベントを1回としてカウントする。

5　警告イベントの保存タイミング

リアルタイム画像処理への影響を抑えるため、毎フレーム DB へ書き込むことはしない。

5.1　処理の流れ

カメラ映像取得
  ↓
YOLOによる人物検出
  ↓
SORTによる追跡
  ↓
仮想ライン通過判定
  ↓
方向判定
  ↓
逆方向の場合、reverse_countを1増加
  ↓
しきい値に到達したか判定
  ↓
しきい値到達
  ↓
音声警告
  ↓
detection_logへ保存
  ↓
reverse_countをリセット

5.2　具体例

1人目が逆方向に通過 → reverse_count = 1 → DBへ保存しない
2人目が逆方向に通過 → reverse_count = 2 → DBへ保存しない
3人目が逆方向に通過 → reverse_count = 3
  → 音声警告 → detection_logへ保存 → reverse_countを0にリセット

6　統計情報の保存

statistics は、一定時間の計測が終了した時点で集計結果を保存する。

total_users   = 50
reverse_count = 6
warning_count = 2

計測終了時 → statisticsへ1レコード保存

7　逆走率

逆走率は DB へ保存しない。total_users と reverse_count から計算できるため、冗長なデータの保存を避ける。

7.1　計算式

逆走率 = reverse_count / total_users × 100

7.2　計算例

total_users   = 50
reverse_count = 3

逆走率 = 3 / 50 × 100 = 6%

8　保存しないデータ

以下の情報は現時点では DB に保存しない。

8.1　track_id

SORT による追跡 ID は、方向判定のために使用するが、DB への保存は行わない。個人識別を目的としたデータを保存しないためである。

8.2　confidence

YOLO の検出信頼度は、検出処理には使用するが、現時点では DB への保存は行わない。

8.3　warning カラム

detection_log は「1レコード＝1回の警告イベント」とするため、warning カラムは不要。レコードが存在すること自体が警告発生を意味する。

8.4　reverse_rate

reverse_count と total_users から計算できるため、DB には保存しない。

9　インデックス方針

現時点では追加 INDEX を設定しない。

理由：

- 現時点で想定するデータ量が大きくない

- 複雑な検索を想定していない

- PRIMARY KEY による識別で十分

- 必要になった場合は将来的に日時カラムへの INDEX 追加を検討する

したがって、INDEX：なし

10　外部キー方針

detection_log と statistics の間に外部キーは設定しない。

理由：

- 両テーブルは親子関係ではない

- detection_log は警告イベントを記録するテーブル

- statistics は一定時間の集計結果を記録するテーブル

- それぞれ独立したデータとして扱うため

したがって、FOREIGN KEY：なし

11　ER図

現時点では、detection_log と statistics の間に直接的なリレーションは設定しない。

┌─────────────────────────┐
│ detection_log           │
├─────────────────────────┤
│ PK id                   │
│    detected_at          │
│    reverse_count        │
└─────────────────────────┘

┌─────────────────────────┐
│ statistics              │
├─────────────────────────┤
│ PK id                   │
│    recorded_at          │
│    total_users          │
│    reverse_count        │
│    warning_count        │
└─────────────────────────┘

12　テーブル定義（DDL）

12.1　detection_log

CREATE TABLE detection_log (
    id INTEGER PRIMARY KEY,
    detected_at TEXT NOT NULL,
    reverse_count INTEGER NOT NULL
);

12.2　statistics

CREATE TABLE statistics (
    id INTEGER PRIMARY KEY,
    recorded_at TEXT NOT NULL,
    total_users INTEGER NOT NULL DEFAULT 0,
    reverse_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0
);

13　テーブル一覧

| **項目** | **detection_log** |
| --- | --- |
| 用途 | 警告イベントの記録 |
| 1レコード | 1回の警告 |
| PK | id |
| FK | なし |
| INDEX | なし |
| 保存タイミング | 音声警告発生時 |

| **項目** | **statistics** |
| --- | --- |
| 用途 | 一定時間の統計情報 |
| 1レコード | 1回の統計集計 |
| PK | id |
| FK | なし |
| INDEX | なし |
| 保存タイミング | 計測終了・統計確定時 |

14　設計方針まとめ

- SQLiteを使用する

- detection_logとstatisticsの2テーブルで構成する

- detection_logは1レコードを1回の警告イベントとする

- statisticsは一定時間の集計結果を保存する

- 仮想ラインの通過方向によって逆走を判定する

- 逆方向の通過ごとに逆走カウントを1増加する

- 毎フレームのDB保存は行わない

- 警告発生時にdetection_logへ保存する

- 統計確定時にstatisticsへ保存する

- 逆走率は保存せず、必要時に計算する

- track_idは保存しない

- confidenceは保存しない

- warningカラムは持たない

- 両テーブルのIDはINTEGER PRIMARY KEYとする

- AUTOINCREMENTは使用しない

- 日時はTEXT型で保存する

- 日時形式はYYYY-MM-DD HH:MM:SSとする

- カウント値はINTEGER型とする

- 統計情報のカウント値にはDEFAULT 0を設定する

- 追加INDEXは設定しない

- 外部キーは設定しない

	2026年8月7日　発行	1 / 2