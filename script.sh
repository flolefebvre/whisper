#!/bin/bash

# Simple wrapper script to run audio_to_text.py with virtual environment
# Usage: ./script.sh <audio_file>

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run the Python script with all provided arguments
python "$SCRIPT_DIR/audio_to_text.py" "$@"

# Deactivate is automatic when script exits