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
python csv_to_html.py
```

By default, it reads `snap-export.csv` and outputs `coins.html`.

### Custom Input/Output Files

```bash
python csv_to_html.py my-coins.csv my-collection.html
```

## Output

Open the generated HTML file in any web browser to view your coin collection with:

- Interactive view toggle (list/grid)
- Column sorting with ascending/descending order
- Zoomable coin images on hover (list view)

## Files

- `csv_to_html.py` - Main converter script
- `style.css` - Stylesheet (embedded in generated HTML)
- `script.js` - JavaScript (embedded in generated HTML)
- `snap-export.csv` - Your CoinSnap export (input)
- `coins.html` - Generated collection page (output)

## Screenshot

After running the script, open `coins.html` in your browser to see your collection!

Example: https://benckx.me/coins

## License

MIT
