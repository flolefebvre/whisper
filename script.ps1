# Simple wrapper to run audio_to_text.py with virtual environment
# Usage: .\script.ps1 <audio_file> [model_name] [--output <output_file>]

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$ScriptDir\venv\Scripts\Activate.ps1"

python "$ScriptDir\audio_to_text.py" @args
