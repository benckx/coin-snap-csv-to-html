#!/usr/bin/env python3
"""
CSV to HTML Converter
Reads a CSV file and converts it to a formatted HTML table.
No external libraries required - uses only Python standard library.
"""

import os

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_css():
    """Load CSS from external style.css file."""
    css_path = os.path.join(SCRIPT_DIR, 'style.css')
    with open(css_path, 'r', encoding='utf-8') as css_file:
        return css_file.read()


def load_js():
    """Load JavaScript from external script.js file."""
    js_path = os.path.join(SCRIPT_DIR, 'script.js')
    with open(js_path, 'r', encoding='utf-8') as js_file:
        return js_file.read()


def escape_html(text):
    """Escape special HTML characters to prevent XSS and display issues."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    return text


def parse_csv_line(line):
    """
    Parse a CSV line handling quoted fields that may contain commas.
    Returns a list of fields.
    """
    fields = []
    current_field = ""
    in_quotes = False
    i = 0

    while i < len(line):
        char = line[i]

        if char == '"':
            if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                # Double quote inside quoted field
                current_field += '"'
                i += 1
            else:
                # Toggle quote state
                in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            # Field separator
            fields.append(current_field.strip())
            current_field = ""
        else:
            current_field += char

        i += 1

    # Add the last field
    fields.append(current_field.strip())
    return fields


def is_image_url(text):
    """Check if a text is an image URL."""
    if not text:
        return False
    text_lower = text.lower()
    return text_lower.startswith('http') and any(ext in text_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'])


def create_html_table(csv_filename, html_filename):
    """
    Read CSV file and create an HTML file with a formatted table.

    Args:
        csv_filename: Path to the input CSV file
        html_filename: Path to the output HTML file
    """
    try:
        # Read the CSV file
        with open(csv_filename, 'r', encoding='utf-8') as csv_file:
            lines = csv_file.readlines()

        if not lines:
            print("Error: CSV file is empty")
            return False

        # Parse header
        header = parse_csv_line(lines[0].strip())

        # Columns to skip in the output
        skip_columns = {'Value (MY)', 'Note', 'Custom set', 'Value, USD (CoinSnap)', 'Precious metal weight', 'Melt value, USD'}
        skip_indices = {i for i, col in enumerate(header) if col in skip_columns}

        # Parse data rows
        data_rows = []
        for line_num, line in enumerate(lines[1:], start=2):
            line = line.strip()
            if line:  # Skip empty lines
                row = parse_csv_line(line)
                # Pad row with empty strings if it has fewer columns than header
                while len(row) < len(header):
                    row.append("")
                data_rows.append(row)

        # Load CSS from external file and indent it
        css_content = load_css()
        css_indented = '\n'.join('        ' + line if line.strip() else line for line in css_content.rstrip().split('\n'))

        # Load JS from external file and indent it
        js_content = load_js()
        js_indented = '\n'.join('        ' + line if line.strip() else line for line in js_content.rstrip().split('\n'))

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coin Collection</title>
    <style>
{css_indented}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Coin Collection</h1>
            <p>Total: {len(data_rows)} coins</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label>View:</label>
                <button class="view-btn active" id="listViewBtn" onclick="setView('list')" title="List View">☰</button>
                <button class="view-btn" id="gridViewBtn" onclick="setView('grid')" title="Grid View">▦</button>
            </div>
            <div class="control-group">
                <label for="sortSelect">Sort by:</label>
                <select id="sortSelect" onchange="sortCoins()">
                    <option value="">-- Select --</option>
                    <option value="country">Country</option>
                    <option value="issuer">Issuer</option>
                    <option value="year">Year</option>
                    <option value="grade">Grade</option>
                    <option value="composition">Composition</option>
                    <option value="value">Value</option>
                </select>
                <button onclick="toggleSortOrder()" id="sortOrderBtn" title="Toggle sort order">↑</button>
            </div>
            <div class="control-group">
                <label for="issuerFilter">Issuer:</label>
                <select id="issuerFilter" onchange="filterCoins()">
                    <option value="">All</option>
                </select>
            </div>
            <div class="control-group">
                <label for="denominationFilter">Denomination:</label>
                <select id="denominationFilter" onchange="filterCoins()">
                    <option value="">All</option>
                </select>
            </div>
        </div>

        <div class="table-container" id="tableContainer">
            <table>
                <thead>
                    <tr>
"""

        # Add table headers
        for idx, col in enumerate(header):
            if idx not in skip_indices:
                html_content += f"                        <th>{escape_html(col)}</th>\n"

        html_content += """                    </tr>
                </thead>
                <tbody id="tableBody">
"""

        # Create a mapping of column names to indices for sortable columns
        col_indices = {col.lower(): i for i, col in enumerate(header)}
        
        def get_cell_value(row, col_name):
            """Get cell value by column name (case-insensitive partial match)."""
            for key, idx in col_indices.items():
                if col_name in key:
                    return row[idx] if idx < len(row) else ""
            return ""

        # Add table rows
        for row_idx, row in enumerate(data_rows):
            # Get sortable data attributes
            country = escape_html(get_cell_value(row, 'country'))
            issuer = escape_html(get_cell_value(row, 'issuer'))
            denomination = escape_html(get_cell_value(row, 'denomination'))
            year = escape_html(get_cell_value(row, 'year'))
            grade = escape_html(get_cell_value(row, 'grade'))
            composition = escape_html(get_cell_value(row, 'composition'))
            value_str = get_cell_value(row, 'value')
            # Extract numeric value for sorting
            value_num = ''.join(c for c in value_str if c.isdigit() or c == '.')
            value_num = value_num if value_num else '0'
            
            html_content += f'                    <tr data-country="{country}" data-issuer="{issuer}" data-denomination="{denomination}" data-year="{year}" data-grade="{grade}" data-composition="{composition}" data-value="{value_num}">\n'
            for idx, cell in enumerate(row):
                # Skip excluded columns
                if idx in skip_indices:
                    continue
                # Check if this column might contain images (based on header)
                col_name = header[idx].lower() if idx < len(header) else ""
                is_photo_col = 'photo' in col_name or 'image' in col_name

                if is_photo_col and is_image_url(cell):
                    # Render as image
                    html_content += f'                        <td class="image-cell"><img src="{escape_html(cell)}" alt="Coin" class="coin-image" loading="lazy"></td>\n'
                elif cell.strip():
                    # Check if it's a value column
                    if 'value' in col_name:
                        html_content += f'                        <td class="value-cell">{escape_html(cell)}</td>\n'
                    elif 'note' in col_name:
                        html_content += f'                        <td class="note-cell" title="{escape_html(cell)}">{escape_html(cell)}</td>\n'
                    else:
                        html_content += f'                        <td>{escape_html(cell)}</td>\n'
                else:
                    # Empty cell
                    html_content += '                        <td class="empty-cell">—</td>\n'
            html_content += "                    </tr>\n"

        html_content += """                </tbody>
            </table>
        </div>

        <div class="grid-container hidden" id="gridContainer">
"""

        # Add grid cards
        for row in data_rows:
            denomination = escape_html(get_cell_value(row, 'denomination'))
            country = escape_html(get_cell_value(row, 'country'))
            issuer = escape_html(get_cell_value(row, 'issuer'))
            year = escape_html(get_cell_value(row, 'year'))
            grade = escape_html(get_cell_value(row, 'grade'))
            composition = escape_html(get_cell_value(row, 'composition'))
            value_display = escape_html(get_cell_value(row, 'value'))
            coinsnap_value = escape_html(get_cell_value(row, 'value, usd (coinsnap)'))
            precious_metal_weight = escape_html(get_cell_value(row, 'precious metal weight'))
            melt_value = escape_html(get_cell_value(row, 'melt value, usd'))
            obverse_url = get_cell_value(row, 'obverse')
            reverse_url = get_cell_value(row, 'reverse')
            value_str = get_cell_value(row, 'value')
            value_num = ''.join(c for c in value_str if c.isdigit() or c == '.')
            value_num = value_num if value_num else '0'

            html_content += f'''            <div class="coin-card" data-country="{country}" data-issuer="{issuer}" data-denomination="{denomination}" data-year="{year}" data-grade="{grade}" data-composition="{composition}" data-value="{value_num}">
                <div class="coin-card-images">
                    <img src="{escape_html(obverse_url)}" alt="Obverse" loading="lazy">
                    <img src="{escape_html(reverse_url)}" alt="Reverse" loading="lazy">
                </div>
                <div class="coin-card-info">
                    <div class="coin-card-title">{denomination}</div>
                    <dl class="coin-card-details">
                        <dt>Country:</dt><dd>{country}</dd>
                        <dt>Issuer:</dt><dd>{issuer}</dd>
                        <dt>Year:</dt><dd>{year}</dd>
                        <dt>Grade:</dt><dd>{grade}</dd>
                        <dt>Composition:</dt><dd>{composition}</dd>'''

            # Add precious metal weight if present
            if precious_metal_weight:
                html_content += f'''
                        <dt>Precious Metal Weight:</dt><dd>{precious_metal_weight}</dd>'''

            # Add melt value if present
            if melt_value:
                html_content += f'''
                        <dt>Melt Value:</dt><dd>{melt_value}</dd>'''

            html_content += f'''
                    </dl>
                    <div class="coin-card-value">{value_display}</div>
                </div>
            </div>
'''

        html_content += """        </div>

        <div class="footer">
            <p>Generated from CSV data</p>
            <p><a href="https://github.com/benckx/coin-snap-csv-to-html" target="_blank">https://github.com/benckx/coin-snap-csv-to-html</a></p>
        </div>
    </div>

    <script>
"""
        html_content += js_indented
        html_content += """
    </script>
</body>
</html>
"""

        # Write HTML file
        with open(html_filename, 'w', encoding='utf-8') as html_file:
            html_file.write(html_content)

        print(f"✅ Successfully converted {csv_filename} to {html_filename}")
        print(f"📊 Processed {len(data_rows)} rows with {len(header)} columns")
        return True

    except FileNotFoundError:
        print(f"❌ Error: Could not find file '{csv_filename}'")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main function to run the CSV to HTML converter."""
    import sys

    # Default filenames
    csv_file = "snap-export.csv"
    html_file = "coins.html"

    # Check if custom filenames were provided as command line arguments
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    if len(sys.argv) > 2:
        html_file = sys.argv[2]

    print("🔄 Converting CSV to HTML...")
    print(f"📥 Input:  {csv_file}")
    print(f"📤 Output: {html_file}")
    print()

    success = create_html_table(csv_file, html_file)

    if success:
        print()
        print(f"🎉 Done! Open {html_file} in your browser to view the coin collection.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
