#!/bin/bash

# Script adapted to the specifics organization of my Linux Mint laptop
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/convert_common.sh"
convert_coinsnap ~/Projects/benckx.me/coins/index.html
