# 開発ルール

SafeStep AI の開発に参加する際は、本ドキュメントのルールに従ってください。

---

# ブランチ運用

## ブランチ構成

```text id="hrwvb5"
main
develop
feature/*
```

| ブランチ        | 用途        |
| ----------- | --------- |
| `main`      | 安定版・リリース版 |
| `develop`   | 開発統合ブランチ  |
| `feature/*` | 機能開発用ブランチ |

---

## 開発フロー

```text id="ccn8d4"
feature/*
   ↓
develop
   ↓
main
```

### ルール

* `main` への直接 push を禁止
* 作業は `feature/*` ブランチで行う
* Pull Request ベースで統合する
* 作業完了後は `develop` へマージする

---

# feature ブランチ命名規則

```text id="9w6m8g"
feature/<機能名>
```

例:

```text id="dgx1g0"
feature/yolo-detection
feature/sort-tracking
feature/wrongway-detection
feature/flask-dashboard
feature/audio-alert
```

---

# コミットメッセージ規約

以下の Prefix を使用してください。

| Prefix      | 内容       |
| ----------- | -------- |
| `feat:`     | 新機能      |
| `fix:`      | バグ修正     |
| `docs:`     | ドキュメント変更 |
| `refactor:` | リファクタリング |
| `test:`     | テスト      |
| `chore:`    | その他      |

---

## コミット例

```text id="9r8k03"
feat: add YOLO person detection
fix: correct tracking ID issue
docs: update README
refactor: simplify detection pipeline
```

---

# Pull Request ルール

## PR タイトル形式

```text id="p2k4z7"
[Feature] 機能名
```

例:

```text id="a1r7c2"
[Feature] YOLO人物検出機能
[Fix] 逆走判定バグ修正
```

---

## PR 前チェック

以下を確認してください。

* 動作確認済み
* 不要なファイルを含んでいない
* `.env` を含んでいない
* ログファイルを含んでいない
* 機密情報を含んでいない

---

# コーディングルール

## Python

* PEP8 準拠
* 関数・変数名は snake_case
* クラス名は PascalCase
* コメントは必要最低限にする

---

# ディレクトリルール

## app/

アプリケーション本体。

```text id="y8n3j4"
detection/   人物検出
tracking/    人物追跡
violation/   逆走判定
audio/       音声関連
dashboard/   Web管理画面
utils/       共通処理
```

---

# セキュリティ・プライバシー

本プロジェクトでは以下を厳守してください。

* 映像データを保存しない
* 個人情報を記録しない
* 顔認識を実装しない
* APIキーを GitHub に push しない

---

# Issue 運用

Issue 作成時は以下を明確に記載してください。

* 内容
* 原因
* 対応方針
* 優先度

---

# その他

大規模変更を行う場合は、事前に Issue または Discussion を作成してください。
