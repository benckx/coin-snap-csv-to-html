#!/bin/bash

# Common conversion logic - called by platform-specific scripts
# Usage: source convert_common.sh <output_html_path>

convert_coinsnap() {
    local OUTPUT_HTML="$1"

    if [ -z "$OUTPUT_HTML" ]; then
        echo "Error: Output path not specified"
        exit 1
    fi

    # Find the most recent CSV file starting with "CoinSnap-Exported-all" in ~/Downloads
    INPUT_CSV=$(ls -t ~/Downloads/CoinSnap-Exported-all*.csv 2>/dev/null | head -1)

    if [ -z "$INPUT_CSV" ]; then
        echo "Error: No CSV file starting with 'CoinSnap-Exported-all' found in ~/Downloads"
        exit 1
    fi

    echo "Using input file: $INPUT_CSV"

    # Ensure output directory exists
    mkdir -p "$(dirname "$OUTPUT_HTML")"

    # Run the Python converter
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    python3 "$SCRIPT_DIR/csv_to_html.py" "$INPUT_CSV" "$OUTPUT_HTML"

    if [ $? -eq 0 ]; then
        echo "Successfully generated: $OUTPUT_HTML"
    else
        echo "Error: Conversion failed"
        exit 1
    fi
}

