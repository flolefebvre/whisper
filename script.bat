@echo off
:: Simple wrapper to run audio_to_text.py with virtual environment
:: Usage: script.bat <audio_file> [model_name] [--output <output_file>]

set SCRIPT_DIR=%~dp0

call "%SCRIPT_DIR%venv\Scripts\activate.bat"

python "%SCRIPT_DIR%audio_to_text.py" %*
