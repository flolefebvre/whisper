# audio-to-text

Transcribe French audio files to text using [OpenAI Whisper](https://github.com/openai/whisper) with GPU acceleration.

**Supports**: M4A, MP3, WAV, FLAC, AAC, OGG
**Requires**: NVIDIA GPU with CUDA support (mandatory — will not run on CPU)

---

## Requirements

- NVIDIA GPU with CUDA support (tested on CUDA 12.1+)
- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) installed on your system

---

## Installation

### Step 1 — Install uv

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. If you already have pip, think of uv as a much faster drop-in replacement that also manages Python versions and virtual environments.

**Linux / WSL:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installing, restart your terminal (or follow the instructions printed by the installer to add uv to your PATH).

---

### Step 2 — Install ffmpeg

ffmpeg is required for audio processing.

**Linux / WSL:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**

Install via [Chocolatey](https://chocolatey.org/):
```powershell
choco install ffmpeg
```

Or download manually from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add it to your PATH.

---

### Step 3 — Clone the repository

```bash
git clone git@github.com:flolefebvre/whisper.git
cd whisper
```

---

### Step 4 — Create a virtual environment and install dependencies

**Linux / WSL:**
```bash
uv venv
source venv/bin/activate
uv pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
uv venv
.\venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

> **Note:** The first install downloads PyTorch with CUDA support (~2–3 GB). This may take a few minutes.

---

## Usage

### Quick start (wrapper scripts)

The wrapper scripts activate the virtual environment for you automatically.

**Linux / WSL:**
```bash
./script.sh audio.m4a
```

**Windows (Command Prompt):**
```bat
script.bat audio.m4a
```

**Windows (PowerShell):**
```powershell
.\script.ps1 audio.m4a
```

The transcription is saved next to the input file with a `.txt` extension (e.g. `audio.m4a` → `audio.txt`).

---

### Full usage

```
python audio_to_text.py <audio_file> [model] [options]
```

#### Arguments

| Argument | Description |
|---|---|
| `audio_file` | Path to the audio file to transcribe |
| `model` | Whisper model to use (default: `large-v3`) |

#### Options

| Option | Short | Description |
|---|---|---|
| `--output <file>` | `-o` | Output text file (default: derived from input filename) |
| `--segments [file]` | `-s` | Save timestamped segments as JSON |
| `--words [file]` | `-w` | Save word-level timestamps as JSON |
| `--json-sentences [file]` | `-j` | Save sentence-level segments as JSON |

#### Available models

| Model | Size | Speed | Accuracy |
|---|---|---|---|
| `tiny` | ~75 MB | Fastest | Lowest |
| `base` | ~145 MB | Fast | Low |
| `small` | ~466 MB | Moderate | Moderate |
| `medium` | ~1.5 GB | Slow | Good |
| `large` | ~2.9 GB | Slower | Great |
| `large-v2` | ~2.9 GB | Slower | Great |
| `large-v3` | ~2.9 GB | Slowest | Best (default) |

---

### Examples

**Basic transcription:**
```bash
python audio_to_text.py recording.m4a
# Output: recording.txt
```

**Use a faster model:**
```bash
python audio_to_text.py recording.m4a small
# Output: recording.txt
```

**Specify output file:**
```bash
python audio_to_text.py recording.m4a --output transcript.txt
```

**Save timestamped segments:**
```bash
python audio_to_text.py recording.m4a --segments
# Output: recording.txt + recording.segments.json
```

**Save word-level timestamps:**
```bash
python audio_to_text.py recording.m4a --words
# Output: recording.txt + recording.words.json
```

**Save sentence-level JSON (useful for subtitles / downstream processing):**
```bash
python audio_to_text.py recording.m4a --json-sentences
# Output: recording.txt + recording.json
```

**All outputs at once:**
```bash
python audio_to_text.py recording.m4a --segments --words --json-sentences
```

**Custom output paths:**
```bash
python audio_to_text.py recording.m4a \
  --output out/transcript.txt \
  --segments out/segments.json \
  --json-sentences out/sentences.json
```

---

## Output formats

**Plain text** (`.txt`): The full transcription as a single block of text.

**Segments JSON** (`--segments`): Whisper's internal segments with start/end timestamps.
```json
[
  { "id": 0, "start": 0.0, "end": 4.2, "text": "Bonjour tout le monde." },
  ...
]
```

**Words JSON** (`--words`): Flattened word-level timestamps.
```json
[
  { "word": "Bonjour", "start": 0.0, "end": 0.5, "probability": 0.98, "segment_id": 0 },
  ...
]
```

**Sentences JSON** (`--json-sentences`): Sentence-level segments (punctuation-based splitting with word timestamps).
```json
{
  "duration": 120.4,
  "language": "french",
  "segments": [
    { "id": 1, "start": 0.0, "end": 4.2, "text": "Bonjour tout le monde." },
    ...
  ]
}
```
