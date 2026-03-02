#!/usr/bin/env python3
"""
Fetch missing details for Numista matches.

For every numista_match row where:
  - category = 'Standard circulation coins'
  - AND any of year_from, year_to, composition, weight, diameter, thickness is NULL

Fetches https://en.numista.com/<numista_id>, parses the
#fiche_caracteristiques section, and updates the row.
"""

import os
import random
import sqlite3
import sys
import time
import urllib.request

from numista_parser import NumistaDetailParser

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(SCRIPT_DIR, "coins.db")

MAX_RETRIES = 5
RETRY_WAIT_SECONDS = [5, 10, 20, 40, 60]

NUMISTA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# HTTP helper
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



# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def fetch_details(conn):
    rows = conn.execute(
        """SELECT id, numista_id
           FROM numista_match
           WHERE category = 'Standard circulation coins'
             AND (
                 issuer           IS NULL OR
                 period           IS NULL OR
                 ruling_authority IS NULL OR
                 year_from        IS NULL OR
                 year_to          IS NULL OR
                 composition      IS NULL OR
                 weight           IS NULL OR
                 diameter         IS NULL OR
                 thickness        IS NULL
             )
           ORDER BY id""",
    ).fetchall()

    if not rows:
        print("✅  Nothing to update.")
        return

    print(f"🔍  {len(rows)} row(s) to fetch details for …\n")

    for match_id, numista_id in rows:
        url = f"https://en.numista.com/{numista_id}"
        print(f"  [{match_id}] numista_id={numista_id}  →  {url}")

        try:
            html = fetch_url(url)
        except RuntimeError as e:
            print(f"  ❌  {e}")
            print("  Stopping – re-run the script to continue.")
            break

        parser = NumistaDetailParser()
        parser.feed(html)

        print(f"       issuer={parser.issuer}  period={parser.period}  "
              f"ruling_authority={parser.ruling_authority}  "
              f"years={parser.year_from}-{parser.year_to}  "
              f"composition={parser.composition}  "
              f"weight={parser.weight}g  "
              f"diameter={parser.diameter}mm  "
              f"thickness={parser.thickness}mm")

        conn.execute(
            """UPDATE numista_match
               SET issuer            = COALESCE(issuer,            ?),
                   period            = COALESCE(period,            ?),
                   ruling_authority  = COALESCE(ruling_authority,  ?),
                   year_from         = COALESCE(year_from,         ?),
                   year_to           = COALESCE(year_to,           ?),
                   composition       = COALESCE(composition,       ?),
                   weight            = COALESCE(weight,            ?),
                   diameter          = COALESCE(diameter,          ?),
                   thickness         = COALESCE(thickness,         ?)
               WHERE id = ?""",
            (parser.issuer, parser.period, parser.ruling_authority,
             parser.year_from, parser.year_to, parser.composition,
             parser.weight, parser.diameter, parser.thickness, match_id),
        )
        conn.commit()

        time.sleep(random.uniform(1, 3))

    total_remaining = conn.execute(
        """SELECT COUNT(*) FROM numista_match
           WHERE category = 'Standard circulation coins'
             AND (issuer IS NULL OR period IS NULL OR ruling_authority IS NULL OR
                  year_from IS NULL OR year_to IS NULL OR composition IS NULL
                  OR weight IS NULL OR diameter IS NULL OR thickness IS NULL)"""
    ).fetchone()[0]
    print(f"\n✅  Done. Rows still incomplete: {total_remaining}")


def main():
    db_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    print(f"🗄️   Database: {db_file}\n")
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")
    fetch_details(conn)
    conn.close()


if __name__ == "__main__":
    main()
