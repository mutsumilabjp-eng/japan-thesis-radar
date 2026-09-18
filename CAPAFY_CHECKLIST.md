# Capafy提出前チェックリスト

提出前に以下を1項目ずつ確認し、未確認のものは正直に「未確認」と記載する。

## 必須項目

- [x] リポジトリが公開（Public）で、Raw URLが認証なしで取得できる
      確認方法: `curl -s -o /dev/null -w "%{http_code}" <Raw URL>` が200を返すこと
- [x] `data/latest.json` のRaw URLがSKILL.md・LISTING.mdに記載されている
- [x] `GOOGLE_SERVICE_ACCOUNT_JSON` に有効なサービスアカウントJSONが登録されている
      経緯: 初回登録時はKeychain項目がhex(16進)エンコードされたまま登録されてしまいパース不能だった。
      hexデコードして正しいJSON（`note-market-research@claude-code-505203.iam.gserviceaccount.com`）を再登録し解消済み。
- [x] 本番Google Sheetsが、上記サービスアカウントのメールアドレスに「閲覧者」共有されている（設定済み）
- [x] `gh workflow run sync.yml` を実行し、実データで同期→集計→commitまで一気通貫で成功することを確認する
      2026-09-18 実行分で成功を確認（run id: 35307028381）。本番シートは現在0件のため、
      同梱モックデータ（12件）を重複除去マージした状態で `data/latest.json` を生成、差分なしのためcommitはスキップ。
- [x] 実データ0件（見出し行のみ）でも `build_dataset.py` がクラッシュせず、空配列のJSONを生成することをローカルで確認済み
- [x] Sheets同期・集計処理が失敗した場合に既存の `data/latest.json` を上書きしないことを確認済み（ローカル・GitHub Actions実行の両方で確認）
- [x] `source_url` による重複除去ロジックが動作することを単体テストで確認済み
- [x] UIが日本語で文字化けなく表示されることをブラウザで確認済み（前回セッション）
- [x] 免責文言がUIフッターに表示されている

## 提出前の最終確認（Capafy固有）

- [ ] Capafyの実際の投稿・提出フォーム上でSKILL.md/LISTING.mdの内容が想定通り表示されるか（未確認・Capafy側の画面が手元にないため）
- [ ] Capafyが `data/latest.json` のRaw URLを定期的にポーリングする想定か、Webhook通知が必要かの仕様確認（未確認）
- [ ] コンセンサス集計・投資家ランキング・強気/弱気人数比較など、要求仕様で禁止された機能が実装に含まれていないことの最終目視確認
      → `scripts/build_dataset.py` を確認した限り該当ロジックなし（件数集計と新規/継続/消滅の論点比較のみ）

## 既知の残タスク（更新: 2026-09-18）

1. 本番Google Sheetsに実データ（Grok等による投稿収集結果）を入れる。現状は見出し行のみで0件。
2. 本番シートに実データが入り次第、リポジトリに残っている同梱モックデータ（`data/raw_posts.json`・`data/latest.json`の12件）をクリアするか判断する。現状の重複除去マージ仕様では、実データが入ってもモックの12件は`source_url`が異なるため消えずに残り続ける。デモ用として残すか、本番切替時に削除するかはユーザー判断。
3. Capafy提出フォーム自体でのSKILL.md/LISTING.mdの表示確認（未確認）
4. Capafyが `data/latest.json` のRaw URLをどう取得する想定か（ポーリング/Webhook）の仕様確認（未確認）
