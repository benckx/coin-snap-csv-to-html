"""
HTML parser for Numista search result pages.
"""

import re
from html.parser import HTMLParser


class NumistaParser(HTMLParser):
    """
    Extract Numista coin IDs, categories, and KM numbers from search results.

    Each result is wrapped in <div class="...description_piece...">. Inside:
    - coin ID: from <a href="/10739">
    - category: from <em>Coins › Standard circulation coins</em> ("Coins › " stripped)
    - KM number: from plain text containing "KM# 67" (first KM# occurrence)
    """

    def __init__(self):
        super().__init__()
        self.results = []          # list of (numista_id, category, km_number, title)
        self._in_desc = False
        self._desc_depth = 0
        self._current_id = None
        self._current_category = None
        self._current_km = None
        self._current_title = None
        self._in_em = False
        self._em_text = ""
        self._desc_text = ""       # accumulates all text inside description_piece
        self._in_title_anchor = False
        self._title_text = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div":
            cls = attrs.get("class", "")
            if "description_piece" in cls:
                self._in_desc = True
                self._desc_depth = 1
                self._current_id = None
                self._current_category = None
                self._current_km = None
                self._current_title = None
                self._desc_text = ""
                self._in_title_anchor = False
                self._title_text = ""
                return
            if self._in_desc:
                self._desc_depth += 1

        if tag == "a" and self._in_desc and self._current_id is None:
            href = attrs.get("href", "")
            m = re.search(r'/catalogue/pieces(\d+)\.html', href)
            if not m:
                m = re.match(r'^/(\d+)$', href)
            if m:
                self._current_id = int(m.group(1))
                self._in_title_anchor = True
                self._title_text = ""

        if tag == "br" and self._in_title_anchor:
            self._title_text += " "

        if tag == "em" and self._in_desc:
            self._in_em = True
            self._em_text = ""

    def handle_data(self, data):
        if self._in_em:
            self._em_text += data
        if self._in_title_anchor:
            self._title_text += data
        if self._in_desc:
            self._desc_text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_title_anchor:
            self._in_title_anchor = False
            # Collapse all whitespace (including newlines from <br>) into single spaces
            self._current_title = " ".join(self._title_text.split())

        if tag == "em" and self._in_em:
            self._in_em = False
            text = self._em_text.strip()
            # Strip leading "Coins › " or "Coins > " prefix (and variants)
            text = re.sub(r'^Coins\s*[›>]\s*', '', text).strip()
            if text:
                self._current_category = text

        if tag == "div" and self._in_desc:
            self._desc_depth -= 1
            if self._desc_depth <= 0:
                self._in_desc = False
                if self._current_id is not None:
                    # Extract KM number from accumulated text, e.g. "KM# 67, Schön# …"
                    km_match = re.search(r'\bKM#\s*(\d+)', self._desc_text)
                    if km_match:
                        self._current_km = int(km_match.group(1))
                    # Avoid duplicates
                    if not any(r[0] == self._current_id for r in self.results):
                        self.results.append((self._current_id, self._current_category, self._current_km, self._current_title))

