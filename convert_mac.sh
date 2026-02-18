#!/bin/bash

# Mac-specific converter script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/convert_common.sh"

convert_coinsnap ~/Dev/hobbies/benckx.me/coins/index.html
