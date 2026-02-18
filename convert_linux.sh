#!/bin/bash

# Linux-specific converter script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/convert_common.sh"

convert_coinsnap /Project/benckx.me/coins/index.html

