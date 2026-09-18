# Japan Thesis Radar

公開されているX（旧Twitter）の日本株関連投稿を、銘柄ごとの「投資論点（テーマ）」と「論点の変化（新規／継続／消滅）」に整理して表示するリサーチツールです。

投資家のコンセンサス集計・ランキング・強気/弱気の人数比較は行いません。あくまで「誰が・いつ・どの銘柄について・どんな論点で発言したか」を、要約と元投稿リンク付きで一覧化するだけのツールです。

## できること

- Google SheetsにためたX投稿データを取り込み、URLで重複除去
- ticker/company名の表記ゆれを正規化（`data/ticker_master.json`）
- 日次・週次・月次の集計と、銘柄ごとの論点集計
- 前期間との差分から「新規論点」「継続論点」「消えた論点」を自動生成
- 日本語100%のシンプルなWeb UI（銘柄一覧／銘柄詳細／論点一覧／投稿者別／新規論点／論点変化）

## ディレクトリ構成

```
japan-thesis-radar/
├── scripts/
│   ├── sync_sheets.py     # Google Sheets → data/raw_posts.json（重複除去済み）
│   └── build_dataset.py   # data/raw_posts.json → data/latest.json（集計・差分）
├── data/
│   ├── latest.json          # 画面が読み込む最終データ（モック同梱済み）
│   ├── raw_posts.json       # 取得済みの生データ（モック同梱済み）
│   └── ticker_master.json   # ticker/company正規化テーブル
├── app/
│   └── index.html         # 静的1ファイルUI
└── .github/workflows/sync.yml  # 3時間ごとの自動同期
```

## ローカルでの動作確認（APIキー不要）

モックデータ（`data/raw_posts.json` と `data/latest.json`）を同梱しているので、Sheets接続なしでもすぐに画面を確認できます。

```bash
cd japan-thesis-radar
python3 -m http.server 8765
```

ブラウザで `http://localhost:8765/app/index.html` を開いてください。

## Google Sheetsの列仕様（固定スキーマ・1行1投稿）

本番シート: https://docs.google.com/spreadsheets/d/1rN-3ZqLWvd-E0kRN15vYAuCyaUGANmHWL4HjvwyMIqc/edit （スプレッドシートID: `1rN-3ZqLWvd-E0kRN15vYAuCyaUGANmHWL4HjvwyMIqc`）

以下の11列を持つシートを用意してください（列の順序は問いません、ヘッダー名で読み取ります）。**1行＝1投稿**の固定スキーマです。Grok等が追記する場合も、この形式のまま2行目以降に1件ずつ追加してください（見出し行の変更・列の追加削除・セル結合はしないでください）。

| 列名 | 内容 |
|---|---|
| collected_at | データ収集日時 |
| handle | 投稿者のXハンドル |
| display_name | 投稿者の表示名 |
| ticker | 証券コード（わかる範囲で） |
| company | 会社名 |
| post_created_at | 投稿日時（ISO8601推奨、例: `2026-09-15T10:00:00+09:00`） |
| post_text | 投稿本文（社内保管用。画面には表示しません） |
| source_url | 元投稿のURL（重複除去のキーになります。必須） |
| topic | 論点（例: AI需要、中国規制、受注回復など） |
| stance | `追い風` / `懸念` / `事実言及` / `判断不明` のいずれか |
| summary | 短い要約（画面に表示されます） |

Grok向け追記ルール：
- 1回の追記＝1行。複数投稿をまとめて1セルに書かない。
- `source_url` が空の行は同期時に無視されるため、必ず埋める。
- `stance` は上記4値以外を書いた場合、自動的に「判断不明」として扱われる。
- 行数がゼロ（見出し行のみ）でも同期・集計処理は正常に完了し、`data/latest.json` は空配列で生成される（動作確認済み）。

## Google Sheets接続方法

1. Google Cloud ConsoleでサービスアカウントJSONキーを発行する。
2. 上記の本番シートを、サービスアカウントのメールアドレス（`xxx@xxx.iam.gserviceaccount.com`）に「閲覧者」として共有する。
3. `.env.example` を参考に環境変数を設定する：
   - `GOOGLE_SERVICE_ACCOUNT_JSON` … サービスアカウントJSONの中身をそのまま1つの環境変数に入れる
   - `GOOGLE_SHEETS_SPREADSHEET_ID` … `1rN-3ZqLWvd-E0kRN15vYAuCyaUGANmHWL4HjvwyMIqc`（本番シートのID。スプレッドシートURLの `/d/` と `/edit` の間の文字列）
   - `GOOGLE_SHEETS_WORKSHEET_NAME` … シート名（省略時は1枚目のシートを自動で使うため、通常は設定不要）
4. ローカルで実行する場合:

```bash
pip install -r requirements.txt
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service_account.json)"
export GOOGLE_SHEETS_SPREADSHEET_ID="your_spreadsheet_id"
python3 scripts/sync_sheets.py
python3 scripts/build_dataset.py
```

Sheets取得や集計処理でエラーが起きた場合、既存の `data/raw_posts.json` / `data/latest.json` は書き換えられません（処理はエラーで停止し、直前の正常なデータがそのまま残ります）。

## GitHub Actionsでの自動同期

`.github/workflows/sync.yml` が3時間ごと（`workflow_dispatch` でも手動実行可）に以下を実行します。

1. `scripts/sync_sheets.py` でSheetsから同期
2. `scripts/build_dataset.py` で集計・差分計算
3. `data/` に差分がある場合のみ commit & push

リポジトリの Settings > Secrets and variables > Actions に以下を登録してください。

- `GOOGLE_SERVICE_ACCOUNT_JSON`（必須。サービスアカウントJSONの中身をそのまま登録）
- `GOOGLE_SHEETS_SPREADSHEET_ID`（必須。設定済み: `1rN-3ZqLWvd-E0kRN15vYAuCyaUGANmHWL4HjvwyMIqc`）
- `GOOGLE_SHEETS_WORKSHEET_NAME`（任意。未設定なら1枚目のシートを自動使用）

登録コマンド例（値を画面に出さずに登録する場合）:

```bash
gh secret set GOOGLE_SERVICE_ACCOUNT_JSON --repo mutsumilabjp-eng/japan-thesis-radar < service_account.json
```

手動で同期を試したい場合は `gh workflow run sync.yml --repo mutsumilabjp-eng/japan-thesis-radar` で即時実行できます。

## 免責事項

本ツールは公開情報を整理するリサーチツールであり、投資助言・売買推奨・将来の株価予測を目的とするものではありません。分類・要約はAIおよび自動処理によるものであり、誤りが含まれる可能性があります。投資判断にあたっては、必ず元投稿・一次情報をご自身でご確認ください。
