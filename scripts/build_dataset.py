#!/usr/bin/env python3
"""data/raw_posts.json + data/ticker_master.json から data/latest.json を再生成する。

- ticker/companyの正規化
- 直近window_days(既定30日)の集計
- 前回のlatest.jsonとの差分から新規論点/継続論点/消えた論点(topic_changes)を算出
- 例外発生時は既存のdata/latest.jsonを一切書き換えない(アトミックwrite)
"""
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_POSTS_PATH = DATA_DIR / "raw_posts.json"
TICKER_MASTER_PATH = DATA_DIR / "ticker_master.json"
LATEST_PATH = DATA_DIR / "latest.json"
PREVIOUS_PATH = DATA_DIR / "latest.previous.json"

WINDOW_DAYS = 30
WEEK_DAYS = 7


def parse_datetime(value: str):
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def build_alias_lookup(ticker_master: dict) -> dict:
    lookup = {}
    for ticker, info in ticker_master.items():
        lookup[ticker] = ticker
        canonical = info.get("company", "")
        if canonical:
            lookup[canonical] = ticker
        for alias in info.get("aliases", []):
            lookup[alias] = ticker
    return lookup


def normalize_record(row: dict, ticker_master: dict, alias_lookup: dict) -> dict | None:
    raw_ticker = (row.get("ticker") or "").strip()
    raw_company = (row.get("company") or "").strip()

    ticker = None
    if raw_ticker and raw_ticker in ticker_master:
        ticker = raw_ticker
    elif raw_ticker in alias_lookup:
        ticker = alias_lookup[raw_ticker]
    elif raw_company in alias_lookup:
        ticker = alias_lookup[raw_company]
    else:
        ticker = raw_ticker or None

    if ticker and ticker in ticker_master:
        company = ticker_master[ticker]["company"]
    else:
        company = raw_company or "不明"
        ticker = ticker or "UNKNOWN"

    stance = (row.get("stance") or "判断不明").strip()
    if stance not in {"追い風", "懸念", "事実言及", "判断不明"}:
        stance = "判断不明"

    return {
        "handle": (row.get("handle") or "").strip(),
        "display_name": (row.get("display_name") or "").strip(),
        "ticker": ticker,
        "company": company,
        "post_created_at": (row.get("post_created_at") or "").strip(),
        "source_url": (row.get("source_url") or "").strip(),
        "topic": (row.get("topic") or "").strip() or "未分類",
        "stance": stance,
        "summary": (row.get("summary") or "").strip(),
    }


def in_window(record: dict, now: datetime, days: int) -> bool:
    dt = parse_datetime(record.get("post_created_at", ""))
    if dt is None:
        return False
    return now - timedelta(days=days) <= dt <= now


def aggregate_topics_by_ticker(records: list[dict]) -> dict:
    result: dict[str, dict[str, int]] = {}
    for r in records:
        ticker = r["ticker"]
        topic = r["topic"]
        result.setdefault(ticker, {})
        result[ticker][topic] = result[ticker].get(topic, 0) + 1
    return result


def build_tickers_list(records: list[dict], ticker_master: dict) -> list[dict]:
    topic_counts = aggregate_topics_by_ticker(records)
    company_by_ticker = {}
    for r in records:
        company_by_ticker.setdefault(r["ticker"], r["company"])

    tickers = []
    for ticker, topics in topic_counts.items():
        topic_list = [
            {"topic": topic, "count": count}
            for topic, count in sorted(topics.items(), key=lambda kv: kv[1], reverse=True)
        ]
        tickers.append({
            "ticker": ticker,
            "company": company_by_ticker.get(ticker, ticker_master.get(ticker, {}).get("company", ticker)),
            "topics": topic_list,
        })
    tickers.sort(key=lambda t: sum(x["count"] for x in t["topics"]), reverse=True)
    return tickers


def build_topics_list(records: list[dict]) -> list[dict]:
    topic_map: dict[str, dict] = {}
    for r in records:
        topic = r["topic"]
        entry = topic_map.setdefault(topic, {"topic": topic, "tickers": set(), "total_count": 0})
        entry["tickers"].add(r["ticker"])
        entry["total_count"] += 1
    topics = [
        {"topic": t["topic"], "tickers": sorted(t["tickers"]), "total_count": t["total_count"]}
        for t in topic_map.values()
    ]
    topics.sort(key=lambda t: t["total_count"], reverse=True)
    return topics


def build_authors_list(records: list[dict]) -> list[dict]:
    author_map: dict[str, dict] = {}
    for r in records:
        handle = r["handle"] or "unknown"
        entry = author_map.setdefault(handle, {
            "handle": handle,
            "display_name": r["display_name"],
            "post_count": 0,
        })
        entry["post_count"] += 1
    authors = list(author_map.values())
    authors.sort(key=lambda a: a["post_count"], reverse=True)
    return authors


def build_topic_changes(current_week_records: list[dict], previous_week_records: list[dict], ticker_master: dict) -> list[dict]:
    current_topics = aggregate_topics_by_ticker(current_week_records)
    previous_topics = aggregate_topics_by_ticker(previous_week_records)

    company_by_ticker = {}
    for r in current_week_records + previous_week_records:
        company_by_ticker.setdefault(r["ticker"], r["company"])

    all_tickers = set(current_topics) | set(previous_topics)
    changes = []
    for ticker in all_tickers:
        cur = set(current_topics.get(ticker, {}))
        prev = set(previous_topics.get(ticker, {}))
        new_topics = sorted(cur - prev)
        disappeared_topics = sorted(prev - cur)
        continuing_topics = sorted(cur & prev)
        if not new_topics and not disappeared_topics and not continuing_topics:
            continue
        changes.append({
            "ticker": ticker,
            "company": company_by_ticker.get(ticker, ticker_master.get(ticker, {}).get("company", ticker)),
            "new_topics": new_topics,
            "continuing_topics": continuing_topics,
            "disappeared_topics": disappeared_topics,
        })
    changes.sort(key=lambda c: (len(c["new_topics"]) + len(c["disappeared_topics"])), reverse=True)
    return changes


def main() -> int:
    now = datetime.now(timezone.utc)

    raw_rows = load_json(RAW_POSTS_PATH, [])
    ticker_master = load_json(TICKER_MASTER_PATH, {})

    if not isinstance(raw_rows, list):
        print("[build_dataset] raw_posts.json の形式が不正です", file=sys.stderr)
        return 1

    alias_lookup = build_alias_lookup(ticker_master)
    normalized = [normalize_record(row, ticker_master, alias_lookup) for row in raw_rows]

    # source_urlが空のレコードは除外(壊れた行の混入対策)
    normalized = [r for r in normalized if r.get("source_url")]

    window_records = [r for r in normalized if in_window(r, now, WINDOW_DAYS)]
    window_records.sort(key=lambda r: r.get("post_created_at", ""), reverse=True)

    current_week_records = [r for r in normalized if in_window(r, now, WEEK_DAYS)]
    previous_week_records = [
        r for r in normalized
        if parse_datetime(r.get("post_created_at", "")) is not None
        and now - timedelta(days=WEEK_DAYS * 2) <= parse_datetime(r["post_created_at"]) < now - timedelta(days=WEEK_DAYS)
    ]

    tickers = build_tickers_list(window_records, ticker_master)
    topics = build_topics_list(window_records)
    authors = build_authors_list(window_records)
    topic_changes = build_topic_changes(current_week_records, previous_week_records, ticker_master)

    new_dataset = {
        "updated_at": now.isoformat(),
        "window_days": WINDOW_DAYS,
        "tickers": tickers,
        "topics": topics,
        "authors": authors,
        "records": window_records,
        "topic_changes": topic_changes,
    }

    # 前回生成物を退避してから新しいlatest.jsonを書く(既存latest.jsonが無ければスキップ)
    if LATEST_PATH.exists():
        shutil.copyfile(LATEST_PATH, PREVIOUS_PATH)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = LATEST_PATH.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(new_dataset, f, ensure_ascii=False, indent=2)
    tmp_path.replace(LATEST_PATH)

    print(f"[build_dataset] 銘柄{len(tickers)}件、論点{len(topics)}件、投稿者{len(authors)}件、レコード{len(window_records)}件を保存しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
