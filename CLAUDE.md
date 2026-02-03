# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GPU-accelerated audio-to-text transcription tool using OpenAI Whisper, optimized for French language audio processing. The project requires NVIDIA GPU with CUDA support and will fail gracefully if GPU is not available.

## Hardware Requirements

- NVIDIA GPU with CUDA support (tested with RTX 4070 16GB)
- CUDA 12.1+ (tested with CUDA 12.9)
- Platform: Ubuntu WSL with CUDA support

## Development Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies with CUDA-enabled PyTorch
pip install -r requirements.txt
```

## Running the Application

```bash
# Using the shell wrapper (recommended)
./script.sh <audio_file> [model_name] [--output <output_file>]

# Direct Python execution
python audio_to_text.py <audio_file> [model_name] [--output <output_file>]

# Example with default model (large-v3)
./script.sh audio.m4a

# Example with specific model
./script.sh audio.m4a medium

# Example with custom output path
./script.sh audio.m4a large-v3 --output transcript.txt
```

### Model Options
- `tiny`, `base`, `small`, `medium`, `large`, `large-v2`, `large-v3` (default)
- Larger models provide better accuracy but require more GPU memory

### Supported Audio Formats
M4A, MP3, WAV, FLAC, AAC, OGG

## Architecture

The application is a single-file CLI tool (`audio_to_text.py`) with a clear execution pipeline:

1. **GPU Validation** (`check_gpu_availability`): Mandatory CUDA GPU check - fails if unavailable
2. **Audio Validation** (`validate_audio_file`): File existence and format verification
3. **Model Loading** (`load_whisper_model`): Loads specified Whisper model onto GPU
4. **Transcription** (`transcribe_audio`): Processes audio with French language optimization
5. **Output** (`save_transcription`): Saves transcription to text file

### Key Configuration

The transcription function (audio_to_text.py:62-98) is pre-configured for French audio with specific Whisper parameters:
- Language: French (forced)
- FP16 precision enabled for GPU efficiency
- Beam size: 5 (balance between quality and speed)
- Temperature: 0.0 (deterministic output)
- Warns if detected language differs from French

### Output Behavior

- Default output derives from input filename (e.g., `audio.m4a` → `audio.txt`)
- If input is already `.txt`, appends `.out.txt` to prevent overwriting
- Output directories are created automatically if they don't exist
- All transcriptions use UTF-8 encoding

## Dependencies

Core dependencies use PyTorch with CUDA 12.1 support:
- `torch`, `torchaudio`, `torchvision` with `+cu121` suffix
- `openai-whisper` for speech-to-text
- `pydub` and `ffmpeg-python` for audio processing
- Extra index URL required: `https://download.pytorch.org/whl/cu121`

## Error Handling

The application has strict error handling:
- RuntimeError if CUDA GPU not available
- FileNotFoundError if audio file doesn't exist
- ValueError if audio format unsupported
- RuntimeError if model loading or transcription fails
- Warning (not error) if detected language differs from French
