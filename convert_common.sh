#!/bin/bash

# Fetch the latest CSV export from the standard download location (on Mac or Linux) and call the Python script that convert the CSV to a HTML file
# (of which the output path is passed as an argument to this script)

# Usage: convert_common.sh <output_html_path>

convert_coinsnap() {
    local OUTPUT_HTML="$1"

    if [ -z "$OUTPUT_HTML" ]; then
        echo "Error: Output path not specified"
        exit 1
    fi

    # Ensure output directory exists
    mkdir -p "$(dirname "$OUTPUT_HTML")"

    # Run the Python converter
    # (by default it resolves the most recent ~/Downloads/CoinSnap-Exported-all*.csv, falling back to snap-export.csv)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    python3 "$SCRIPT_DIR/csv_to_html.py" "$OUTPUT_HTML"

    if [ $? -eq 0 ]; then
        echo "Successfully generated: $OUTPUT_HTML"
    else
        echo "Error: Conversion failed"
        exit 1
    fi
}
