# Coin Collection CSV to HTML Converter

Vibed-coded, quick-and-dirty script to convert your [CoinSnap](https://coinidentifierai.com/) coin collection CSV file
to a beautiful, interactive HTML page.

## Features

- **List View**: Traditional table layout with sortable columns and hover-to-zoom images
- **Grid View**: Card-based layout displaying full-size coin images (323×323)
- **Sorting**: Sort your collection by Country, Issuer, Year, Grade, Composition, or Value
- **Responsive Design**: Works on desktop and mobile devices
- **No Dependencies**: Uses only Python standard library

The output HTML file includes embedded CSS and JavaScript for easy sharing (no external files needed). The CSS and JS
files are listed as separate files on the repo, but just to simplify the Python script; they get included in the final
HTML.

## Usage

1. Export your coin collection from the CoinSnap app (the app lets you send the CSV to an email address)
2. Place the CSV file in the same directory as the script (or specify the path)
3. Run the converter:

```bash
python3 csv_to_html.py
```

By default, it outputs `coins.html`. If no input file is specified, the script will first attempt to resolve the most
recent `CoinSnap-Exported-all*.csv` file from `~/Downloads` (on Mac and Linux), and fall back to `coin-snap-example.csv`
if
none is found.

### Custom Input/Output Files

```bash
python3 csv_to_html.py my-coins.csv my-collection.html
```

## Output

Open the generated HTML file in any web browser to view your coin collection with:

- Interactive view toggle (list/grid)
- Column sorting with ascending/descending order
- Zoomable coin images on hover (list view)

## Files

- `csv_to_html.py` - Main converter script
- `html-includes/style.css` - Stylesheet (embedded in generated HTML)
- `html-includes/script.js` - JavaScript (embedded in generated HTML)
- `coin-snap-example.csv` - CoinSnap export (input of script)
- `coins.html` - Generated collection page (output of script)

## Example

After running the script, open `coins.html` in your browser to see your collection!

Example: https://benckx.me/coins

# Coin Collection CSV to SQLite Database

A secondary workflow that stores the collection in a SQLite database and enriches it with data
from [Numista](https://en.numista.com/).

## Files

- `csv_to_sqlite.py` - CSV to SQLite converter + search Numista for matches
- `fetch_numista_details.py` - Fetches missing coin attributes from Numista
- `numista_parser.py` - HTML parsers for Numista search results and detail pages
- `coin_utils.py` - Shared utilities (CSV helpers, Numista URL builder)

## Usage

### Phase 1 – Import CSV into SQLite

Reads the CoinSnap CSV export and populates a `coin` table (deduplicated, with occurrence counts):

```bash
python3 csv_to_sqlite.py
```

The script accepts the same optional CSV path argument as `csv_to_html.py`. The database is written to `coins.db`.

### Phase 2 – Fetch Numista matches

For each coin in the database that doesn't yet have enough Numista candidates, searches Numista and stores the results
in a `numista_match` table. This runs automatically after Phase 1.

### Fetch coin details

For every `numista_match` row whose category is `Standard circulation coins` and that is missing any of `issuer`,
`period`, `year_from`, `year_to`, `composition`, `weight`, `diameter`, or `thickness`, fetches the Numista detail page
and fills in the missing values:

```bash
python3 fetch_numista_details.py
```

Both scripts accept an optional path to the database file as a first argument (default: `coins.db`).

## Notice on Data Usage & Compliance

This tool is intended strictly for personal, non-commercial use to assist collectors in managing their private records.
It is not designed for mass data harvesting or commercial exploitation. Users are advised that
Numista's [Terms of Use](https://en.numista.com/conditions.php) (Section 10) prohibit abnormal use of the platform.

To ensure respect for Numista's infrastructure:

- This script is rate-limited to minimize server load.
- For extensive data needs or large-scale automation, please use the official Numista API.
- This project is independent and not affiliated with or endorsed by Numista.

# License

MIT
