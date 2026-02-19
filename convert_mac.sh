#!/bin/bash

# Script adapted to the specifics organization of my Macbook
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/convert_common.sh"
convert_coinsnap ~/Dev/hobbies/benckx.me/coins/index.html
