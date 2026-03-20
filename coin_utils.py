"""
Shared utilities for coin scripts.
"""

import glob
import os
import re
import urllib.parse

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_default_csv():
    """Return the most recent CoinSnap CSV export from ~/Downloads, or fall back to coin-snap-example.csv."""
    pattern = os.path.expanduser("~/Downloads/CoinSnap-Exported-all*.csv")
    candidates = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if candidates:
        return candidates[0]
    return os.path.join(_SCRIPT_DIR, "coin-snap-example.csv")


def build_numista_url(issuer, denomination, year, krause_number="", subject="", mintmark=""):
    """Build a Numista search URL for a coin.

    Args:
        issuer: The coin issuer (e.g., "Papal States")
        denomination: The coin denomination (e.g., "10 soldi")
        year: The coin year (e.g., "1867")
        krause_number: Optional Krause number (e.g., "KM# 38" or "38")
        subject: Optional subject (appended to search when not "Common series")
        mintmark: Optional mintmark (appended to search when not "No mintmark")

    Returns:
        A Numista search URL
    """
    # Normalize issuer names for Numista
    issuer = issuer.replace("Western Africa (BCEAO)", "BCEAO")

    # Normalize denomination spelling for Numista
    denomination = denomination.replace("kopeks", "kopecks").replace("kopek", "kopeck")
    denomination = denomination.replace("rubles", "roubles").replace("ruble", "rouble")
    # Remove parenthetical alternate names (e.g. "2 shillings (florin)" → "2 shillings")
    denomination = re.sub(r"\s*\(.*?\)", "", denomination).strip()

    # Extract KM number if available.
    # Numista's `no=` param IS the KM/Krause number filter.
    km_num = ""
    if krause_number:
        km_num = krause_number.replace("KM#", "").replace("KM #", "").strip()

    # When a KM number is known, put it in `no=` and only search by issuer.
    # Adding denomination/year to `r=` can hurt results due to spelling mismatches.
    if km_num:
        search_parts = [issuer, year]
    else:
        search_parts = [issuer, denomination, year]
        if subject and subject.strip().lower() != "common series":
            search_parts.append(subject.strip())
        if mintmark and mintmark.strip().lower() != "no mintmark":
            search_parts.append(mintmark.strip())

    encoded_query = urllib.parse.quote_plus(" ".join(search_parts))
    no_param = urllib.parse.quote_plus(km_num)

    return (
        f"https://en.numista.com/catalogue/index.php?r={encoded_query}"
        f"&st=147&cat=y&im1=&im2=&ru=&ie=&ca=3&no={no_param}&v=&cu=&a=&dg=&i=&b=&m=&f=&t=&t2=&w=&mt=&u=&g=&c=&wi=&sw="
    )
