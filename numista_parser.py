"""
HTML parser for Numista search result and detail pages.
"""

import re
from html.parser import HTMLParser


class NumistaSearchResultParser(HTMLParser):
    """
    Extract Numista coin IDs, categories, and KM numbers from search results.

    Each result is wrapped in <div class="...description_piece...">. Inside:
    - coin ID: from <a href="/10739">
    - category: from <em>Coins › Standard circulation coins</em> ("Coins › " stripped)
    - KM number: from plain text containing "KM# 67" (first KM# occurrence)
    """

    def __init__(self):
        super().__init__()
        self.results = []          # list of (numista_id, category, km_number, title, year_from, year_to)
        self._in_desc = False
        self._desc_depth = 0
        self._current_id = None
        self._current_category = None
        self._current_km = None
        self._current_title = None
        self._current_year_from = None
        self._current_year_to = None
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
                self._current_year_from = None
                self._current_year_to = None
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
                        self.results.append((self._current_id, self._current_category, self._current_km, self._current_title, self._current_year_from, self._current_year_to))


class NumistaDetailParser(HTMLParser):
    """
    Parse https://en.numista.com/<id> and extract from #fiche_caracteristiques:
      - year_from, year_to  (from the "Years" row)
      - composition         (from the "Composition" row)
      - weight              (from the "Weight" row, in grams)
      - diameter            (from the "Diameter" row, in mm)
      - thickness           (from the "Thickness" row, in mm)
    """

    def __init__(self):
        super().__init__()
        self.year_from = None
        self.year_to = None
        self.issuer = None
        self.period = None
        self.ruling_authority = None
        self.composition = None
        self.weight = None
        self.diameter = None
        self.thickness = None

        self._in_section = False
        self._in_th = False
        self._in_td = False
        self._current_th = ""
        self._td_text = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and attrs.get("id") == "fiche_caracteristiques":
            self._in_section = True
            return
        if not self._in_section:
            return
        if tag == "th":
            self._in_th = True
            self._current_th = ""
        if tag == "td":
            self._in_td = True
            self._td_text = ""

    def handle_data(self, data):
        if self._in_th:
            self._current_th += data
        if self._in_td:
            self._td_text += data

    def handle_endtag(self, tag):
        if tag == "section" and self._in_section:
            self._in_section = False
            return
        if not self._in_section:
            return
        if tag == "th":
            self._in_th = False
            self._current_th = self._current_th.strip()
        if tag == "td":
            self._in_td = False
            value = " ".join(self._td_text.split())
            self._handle_field(self._current_th, value)

    def _handle_field(self, label, value):
        if label == "Issuer":
            self.issuer = value.strip() or None

        elif label == "Period":
            self.period = value.strip() or None

        elif label == "Ruling authority":
            self.ruling_authority = value.strip() or None

        if label in ("Years", "Year"):
            # e.g. "1998-2024", "1998–2024", or "1998" / "1944"
            m = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', value)
            if m:
                self.year_from = int(m.group(1))
                self.year_to = int(m.group(2))
            else:
                m = re.search(r'(\d{4})', value)
                if m:
                    self.year_from = int(m.group(1))
                    self.year_to = int(m.group(1))

        elif label == "Composition":
            self.composition = value.strip() or None

        elif label == "Weight":
            m = re.search(r'([\d.]+)', value)
            if m:
                self.weight = float(m.group(1))

        elif label == "Diameter":
            m = re.search(r'([\d.]+)', value)
            if m:
                self.diameter = float(m.group(1))

        elif label == "Thickness":
            m = re.search(r'([\d.]+)', value)
            if m:
                self.thickness = float(m.group(1))

