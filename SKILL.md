# Japan Thesis Radar

## 概要

日本株について公開されているX投稿を収集・整理し、銘柄ごとの「投資論点」とその時系列変化（新規に出てきた論点／継続している論点／消えた論点）を一覧化するリサーチAgentです。

コンセンサス集計、強気/弱気の人数比較、投資家ランキングは行いません。個々の投稿を論点単位で整理し、要約と元投稿リンクを提示するところまでを役割とします。

## 入力

- Google Sheets（1シート、以下11列）
  - `collected_at` / `handle` / `display_name` / `ticker` / `company` / `post_created_at` / `post_text` / `source_url` / `topic` / `stance` / `summary`
  - `stance` は `追い風` / `懸念` / `事実言及` / `判断不明` のいずれか

## 処理フロー

1. Google Sheetsから全行を取得
2. `source_url` を一意キーとして重複除去
3. `ticker` / `company` の表記ゆれを正規化テーブル（`data/ticker_master.json`）で統一
4. 日次・週次・月次の集計ウィンドウを計算
5. 銘柄ごとに論点（topic）の件数を集計
6. 直近1週間と前週の論点セットを比較し、新規論点・継続論点・消えた論点を算出
7. `data/latest.json` に保存

## 出力

- `data/latest.json`：Web UIが読み込む集計済みデータ（銘柄一覧、論点一覧、投稿者一覧、投稿レコード、論点変化）
- `app/index.html`：日本語UI（銘柄一覧／銘柄詳細／論点一覧／投稿者別／新規論点／論点変化）

## 使い方

1. `pip install -r requirements.txt`
2. Google Sheetsのサービスアカウント認証情報を環境変数に設定（詳細はREADME.md参照）
3. `python scripts/sync_sheets.py` でSheetsから同期
4. `python scripts/build_dataset.py` で集計・差分計算
5. `app/index.html` をブラウザで開く（またはGitHub Pagesなどで配信）

APIキー・Sheets接続情報が無い状態でも、同梱のモックデータ（`data/raw_posts.json` / `data/latest.json`）でUIの動作を確認できます。

## 自動更新

GitHub Actions（`.github/workflows/sync.yml`）により3時間ごとに自動同期し、データに変更があった場合のみコミットします。

## 制限事項・注意点

- 本ツールは投資助言・売買推奨・将来予測を行うものではありません。公開情報の整理・要約に特化しています。
- 論点の分類・要約はテキストベースの機械的処理であり、誤りを含む可能性があります。
- 投稿本文の全文転載は行わず、要約と元投稿リンクの提示にとどめています。
- Sheets同期や集計処理が失敗した場合、既存の `data/latest.json` は上書きされません（直前の正常なデータを保持します）。
