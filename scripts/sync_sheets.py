#!/usr/bin/env python3
"""Google SheetsからX投稿の整理データを取得し、URL重複を除去してdata/raw_posts.jsonへ保存する。

失敗時は例外を送出して終了するだけで、data/raw_posts.json や data/latest.json には一切書き込まない。
"""
import json
import os
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "collected_at",
    "handle",
    "display_name",
    "ticker",
    "company",
    "post_created_at",
    "post_text",
    "source_url",
    "topic",
    "stance",
    "summary",
]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_POSTS_PATH = DATA_DIR / "raw_posts.json"


def fetch_rows_from_sheets() -> list[dict]:
    import gspread
    from google.oauth2.service_account import Credentials

    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID")
    worksheet_name = os.environ.get("GOOGLE_SHEETS_WORKSHEET_NAME")

    if not sa_json:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON が設定されていません")
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEETS_SPREADSHEET_ID が設定されていません")

    sa_info = json.loads(sa_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet(worksheet_name) if worksheet_name else sheet.sheet1

    records = worksheet.get_all_records()
    rows = []
    for record in records:
        row = {col: str(record.get(col, "")).strip() for col in REQUIRED_COLUMNS}
        if not row["source_url"]:
            continue
        rows.append(row)
    return rows


def load_existing_raw_posts() -> list[dict]:
    if not RAW_POSTS_PATH.exists():
        return []
    try:
        with RAW_POSTS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def dedupe_by_source_url(rows: list[dict]) -> list[dict]:
    seen = {}
    for row in rows:
        url = row.get("source_url", "").strip()
        if not url:
            continue
        # 後勝ち: 同じURLが複数あれば新しく取得した方(list後方)を採用
        seen[url] = row
    return list(seen.values())


def main() -> int:
    try:
        fetched_rows = fetch_rows_from_sheets()
    except Exception as exc:  # noqa: BLE001 - 意図的に広く捕捉し、既存データを守る
        print(f"[sync_sheets] Sheets取得に失敗しました: {exc}", file=sys.stderr)
        return 1

    existing_rows = load_existing_raw_posts()
    merged = dedupe_by_source_url(existing_rows + fetched_rows)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = RAW_POSTS_PATH.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    tmp_path.replace(RAW_POSTS_PATH)

    print(f"[sync_sheets] {len(fetched_rows)}件取得、重複除去後{len(merged)}件を保存しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
