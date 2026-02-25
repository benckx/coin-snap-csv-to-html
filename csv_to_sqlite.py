#!/usr/bin/env python3
"""
CSV to SQLite Converter + Numista Match Fetcher

Phase 1: Reads the CoinSnap CSV export and populates a SQLite database with
         a 'coin' table (deduplicated, with occurrence counts).

Phase 2: For each coin without enough matches, fetches the Numista search page
         and stores candidate matches in a 'match' table.
"""

import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

from coin_utils import build_numista_url, find_default_csv
from numista_parser import NumistaParser

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(SCRIPT_DIR, "coins.db")

# Minimum matches we want per coin before skipping the Numista fetch
MIN_MATCHES = 1

# Retry settings for HTTP requests
MAX_RETRIES = 5
RETRY_WAIT_SECONDS = [5, 10, 20, 40, 60]  # successive wait times

NUMISTA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ---------------------------------------------------------------------------
# CSV parsing helpers
# ---------------------------------------------------------------------------


def parse_csv_line(line):
    """Parse a CSV line handling quoted fields that may contain commas."""
    fields = []
    current_field = ""
    in_quotes = False
    i = 0
    while i < len(line):
        char = line[i]
        if char == '"':
            if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                current_field += '"'
                i += 1
            else:
                in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            fields.append(current_field.strip())
            current_field = ""
        else:
            current_field += char
        i += 1
    fields.append(current_field.strip())
    return fields


# ---------------------------------------------------------------------------
# Phase 1 – CSV → SQLite
# ---------------------------------------------------------------------------


def setup_database(conn):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS coin (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            issuer      TEXT    NOT NULL,
            year        TEXT    NOT NULL,
            denomination TEXT   NOT NULL,
            km_number   INTEGER,
            mintmark    TEXT,
            subject     TEXT,
            occurrences INTEGER NOT NULL DEFAULT 1,
            composition TEXT,
            weight      REAL,
            diameter    REAL,
            thickness   REAL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_coin_unique
            ON coin (issuer, year, denomination,
                     COALESCE(km_number, -1),
                     COALESCE(mintmark, ''),
                     COALESCE(subject, ''));

        CREATE TABLE IF NOT EXISTS match (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id     INTEGER NOT NULL REFERENCES coin(id),
            numista_id  INTEGER NOT NULL,
            verified    INTEGER NOT NULL DEFAULT 0,
            category    TEXT,
            km_number   INTEGER,
            title       TEXT,
            UNIQUE (coin_id, numista_id)
        );
    """)
    conn.commit()


def parse_km_number(raw):
    """Extract an integer KM number from strings like 'KM# 38' or '38'."""
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", raw)
    return int(digits) if digits else None


def load_csv(csv_filename):
    """Read the CSV and return (header, list-of-dicts)."""
    with open(csv_filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return [], []

    header = parse_csv_line(lines[0].strip())
    col_map = {col.strip().lower(): i for i, col in enumerate(header)}

    def get(row, *keys):
        for k in keys:
            for col, idx in col_map.items():
                if k in col:
                    return row[idx] if idx < len(row) else ""
        return ""

    rows = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        row = parse_csv_line(line)
        while len(row) < len(header):
            row.append("")

        rows.append({
            "issuer": get(row, "issuer"),
            "year": get(row, "year"),
            "denomination": get(row, "denomination"),
            "km_number": parse_km_number(get(row, "krause")),
            "mintmark": get(row, "mintmark") or None,
            "subject": get(row, "subject") or None,
            "composition": get(row, "composition"),
        })

    return rows


def upsert_coins(conn, csv_rows):
    """
    Insert coins from CSV into the 'coin' table.

    - Count occurrences within this CSV run.
    - On re-runs: update 'occurrences' only if the CSV count is larger
      (i.e. we never shrink it, but we do reflect new duplicates in a fresh CSV).
    """
    # Count occurrences within this CSV
    from collections import Counter
    key_of = lambda r: (r["issuer"], r["year"], r["denomination"], r["km_number"], r["mintmark"], r["subject"])
    counts = Counter(key_of(r) for r in csv_rows)

    # Deduplicate: keep first occurrence for attribute values
    seen = {}
    for r in csv_rows:
        k = key_of(r)
        if k not in seen:
            seen[k] = r

    inserted = 0
    updated = 0
    for key, r in seen.items():
        occ = counts[key]
        km = r["km_number"]
        existing = conn.execute(
            """SELECT id, occurrences FROM coin
               WHERE issuer=? AND year=? AND denomination=?
                 AND COALESCE(km_number,-1)=COALESCE(?,-1)
                 AND COALESCE(mintmark,'')=COALESCE(?,'')
                 AND COALESCE(subject,'')=COALESCE(?,'')""",
            (r["issuer"], r["year"], r["denomination"], km, r["mintmark"], r["subject"]),
        ).fetchone()

        if existing is None:
            conn.execute(
                """INSERT INTO coin (issuer, year, denomination, km_number,
                                    mintmark, subject, occurrences, composition)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (r["issuer"], r["year"], r["denomination"], km,
                 r["mintmark"], r["subject"], occ, r["composition"]),
            )
            inserted += 1
        else:
            coin_id, old_occ = existing
            if occ != old_occ:
                conn.execute(
                    "UPDATE coin SET occurrences=? WHERE id=?",
                    (occ, coin_id),
                )
                updated += 1

    conn.commit()
    print(f"Phase 1 ✅  inserted={inserted}  updated={updated}  "
          f"total unique coins={conn.execute('SELECT COUNT(*) FROM coin').fetchone()[0]}")


# ---------------------------------------------------------------------------
# Phase 2 – Numista fetch
# ---------------------------------------------------------------------------



def fetch_url(url, retries=MAX_RETRIES):
    """Fetch a URL with retries. Returns HTML string or raises."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=NUMISTA_HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            wait = RETRY_WAIT_SECONDS[min(attempt, len(RETRY_WAIT_SECONDS) - 1)]
            print(f"  ⚠️  Attempt {attempt + 1}/{retries} failed ({exc}). "
                  f"Retrying in {wait}s …")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


def fetch_numista_matches(conn):
    """
    For every coin that has fewer than MIN_MATCHES matches, query Numista
    and store found IDs in the 'match' table.
    """
    coins = conn.execute(
        """SELECT c.id, c.issuer, c.year, c.denomination,
                  c.km_number,
                  COUNT(m.id) AS match_count
           FROM coin c
           LEFT JOIN match m ON m.coin_id = c.id
           GROUP BY c.id
           HAVING match_count < ?
           ORDER BY c.id""",
        (MIN_MATCHES,),
    ).fetchall()

    if not coins:
        print("Phase 2 ✅  All coins already have enough matches.")
        return

    print(f"Phase 2 🔍  {len(coins)} coin(s) need Numista lookups …\n")

    for row in coins:
        coin_id, issuer, year, denomination, km_number, match_count = row
        km_str = f"KM# {km_number}" if km_number else ""
        url = build_numista_url(issuer, denomination, year, km_str)

        print(f"  [{coin_id}] {issuer} – {denomination} ({year}) {km_str}")
        print(f"       URL: {url}")

        try:
            html = fetch_url(url)
        except RuntimeError as e:
            print(f"  ❌  {e}")
            print("  Stopping Phase 2 – re-run the script to continue.")
            break

        parser = NumistaParser()
        parser.feed(html)
        found = parser.results

        # If KM was specified but returned nothing, retry without KM
        if not found and km_str:
            fallback_url = build_numista_url(issuer, denomination, year, "")
            print(f"       No results with KM – retrying without KM …")
            print(f"       URL: {fallback_url}")
            time.sleep(2)
            try:
                html = fetch_url(fallback_url)
            except RuntimeError as e:
                print(f"  ❌  {e}")
                print("  Stopping Phase 2 – re-run the script to continue.")
                break
            parser = NumistaParser()
            parser.feed(html)
            found = parser.results

        if found:
            print(f"       Found {len(found)} candidate(s): {[r[0] for r in found]}")
            for nid, category, match_km, title in found:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO match (coin_id, numista_id, verified, category, km_number, title) VALUES (?,?,0,?,?,?)",
                        (coin_id, nid, category, match_km, title),
                    )
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
        else:
            print("       No candidates found on Numista for this search.")

        # Polite delay between requests
        time.sleep(2)

    total_matches = conn.execute("SELECT COUNT(*) FROM match").fetchone()[0]
    print(f"\nPhase 2 ✅  Total matches in DB: {total_matches}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    csv_file = sys.argv[1] if len(sys.argv) > 1 else find_default_csv()
    db_file = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DB

    print("🔄  CSV → SQLite + Numista matcher")
    print(f"📥  Input CSV : {csv_file}")
    print(f"🗄️   Database  : {db_file}")
    print()

    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")

    # ── Phase 1 ─────────────────────────────────────────────────────────────
    print("── Phase 1: CSV → coin table ──────────────────────────────────")
    setup_database(conn)
    csv_rows = load_csv(csv_file)
    if not csv_rows:
        print("❌  CSV file is empty or not found.")
        sys.exit(1)
    upsert_coins(conn, csv_rows)
    print()

    # ── Phase 2 ─────────────────────────────────────────────────────────────
    print("── Phase 2: Numista lookup ────────────────────────────────────")
    fetch_numista_matches(conn)

    conn.close()
    print("\n🎉  Done!")


if __name__ == "__main__":
    main()
