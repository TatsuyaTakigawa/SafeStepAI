# SafeStep AI

学校の階段で通行方向を判定し、逆走を検知したときに音声で注意喚起するシステムです。Raspberry Pi のカメラ映像をリアルタイムに処理し、検知イベントを別の Raspberry Pi 上の Web ダッシュボードへ送信します。

> 本プロジェクトは開発中の卒業制作です。判定位置や方向などの値は設置環境に合わせた調整が必要です。安全設備の代替として使用しないでください。

## システム構成

```text
[検知用 Raspberry Pi]
カメラ → YOLOによる人物検出・追跡 → 通行方向／逆走判定
  ├─ 逆走時：音声アラーム
  └─ 検知イベント ── HTTP API ──┐
                                 ↓
[ダッシュボード用 Raspberry Pi]  Webアプリ → MariaDB
                                 └─ ログイン後にイベントを確認
```

検知処理と Web ダッシュボード／データベースは別々に動かす構成です。カメラ映像そのものをダッシュボードへ送る機能はありません。

## 主な機能

- YOLO によるカメラ映像からの人物検出・追跡
- 仮想ラインの通過方向に基づく逆走判定
- 検知用 Raspberry Pi での音声アラーム
- HTTP API 経由での検知イベント送信
- Web ダッシュボードでのイベント確認・集計
- Docker Compose による Web アプリと MariaDB の起動

## リポジトリ構成

```text
.
├── docs/                 # 設計資料・クラス図
├── host/                 # ダッシュボード/API、Docker Compose、DB初期化SQL
│   └── README.md         # ダッシュボード側の構築・運用手順
├── pi/                   # カメラ検知クライアント、アラーム関連スクリプト
├── CONTRIBUTING.md       # 開発ルール
├── LICENSE
└── README.md
```

## 動作環境・使用技術

- Raspberry Pi 5（検知用・ダッシュボード用）
- Raspberry Pi OS 64-bit / ARM64
- USB または Web カメラ（検知用）とスピーカー（アラーム用）
- Docker Engine / Docker Compose plugin（ダッシュボード側）
- Python、Ultralytics YOLO、OpenCV（検知側）
- PHP 8.3 + Apache、MariaDB 11.4（ダッシュボード側）

## セットアップ

### 1. ダッシュボードを起動する

`host/` の手順に従って `.env` と `private/config.php` を設定し、ダッシュボード用 Raspberry Pi で起動してください。

```bash
cd host
cp .env.example .env
# .env の認証情報・APIキーなどを設定
# private/config.php を用意（詳細は host/README.md を参照）
docker compose up -d --build
```

詳しい設定、既存データベースの移行、バックアップ方法は [`host/README.md`](host/README.md) を参照してください。

### 2. 検知用 Raspberry Pi を設定する

1. `pi/` のスクリプトと必要なモデルファイルを検知用 Raspberry Pi に配置します。
2. `pi/start_safestep.sh` のダッシュボード接続先を環境に合わせて設定します。
3. カメラ、音声出力、API キーを準備します。API キーはダッシュボード側の設定と一致させてください。
4. カメラデバイスやモデルの配置を確認して検知プログラムを起動します。

検知スクリプトの `LINE_Y`、`MARGIN`、`NORMAL_DIRECTION` はテスト用の初期値です。カメラの向き・画角・設置位置に応じて調整し、実環境で十分に動作確認してください。運用時の配置や設定の詳細は、各スクリプト内の設定とコメントを確認してください。

## イベントデータ

検知クライアントは、通行方向、逆走フラグ、追跡 ID、端末名、検知時刻を API に送信します。通信には `X-API-Key` ヘッダーを使用します。イベント API の例や DB の取り扱いは [`host/README.md`](host/README.md) を参照してください。

## セキュリティとプライバシー

- `.env`、API キー、ログイン情報などの秘密情報を Git に登録しないでください。
- ダッシュボードは初期設定の HTTP 接続のままインターネットへ直接公開せず、LAN 内または VPN 経由で利用してください。
- 定期的にデータベースをバックアップし、バックアップを Raspberry Pi 本体以外にも保管してください。
- 顔認識を行うシステムではありません。設置・運用時は施設のルールおよびプライバシー要件を確認してください。

## 開発

ブランチ運用、Pull Request、コミットメッセージのルールは [`CONTRIBUTING.md`](CONTRIBUTING.md) を参照してください。

## ライセンス

MIT License。詳細は [`LICENSE`](LICENSE) を参照してください。
