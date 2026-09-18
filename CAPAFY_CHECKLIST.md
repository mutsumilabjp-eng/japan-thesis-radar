# Capafy提出前チェックリスト

提出前に以下を1項目ずつ確認し、未確認のものは正直に「未確認」と記載する。

## 必須項目

- [x] リポジトリが公開（Public）で、Raw URLが認証なしで取得できる
      確認方法: `curl -s -o /dev/null -w "%{http_code}" <Raw URL>` が200を返すこと
- [x] `data/latest.json` のRaw URLがSKILL.md・LISTING.mdに記載されている
- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON` に有効なサービスアカウントJSONが登録されている
      現状: リポジトリSecretsには登録済みだが、値が不正な形式でJSONとしてパースできず、
      GitHub Actions実行時に `Extra data: line 1 column 2` エラーで失敗することを確認済み。
      Google Cloud Consoleで発行した正しいサービスアカウントJSONを再登録する必要がある。
- [ ] 本番Google Sheetsが、上記サービスアカウントのメールアドレスに「閲覧者」共有されている
      （サービスアカウントJSONが未確定のため、共有先メールアドレスも未確定）
- [ ] `gh workflow run sync.yml` を実行し、実データで同期→集計→commitまで一気通貫で成功することを確認する
      現状: 空のシート状態でのテスト実行はSecrets不正により失敗（上記と同じ原因）。原因解消後に再実行して確認する。
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

## 既知の残タスク（このチェックリスト作成時点）

1. 正しい `GOOGLE_SERVICE_ACCOUNT_JSON` の取得・再登録（ユーザー側でGoogle Cloud Consoleから発行）
2. 上記サービスアカウントを本番Google Sheetsに共有
3. 実データでのGitHub Actions実行成功の確認
4. Capafy提出フォーム自体でのSKILL.md/LISTING.mdの表示確認
