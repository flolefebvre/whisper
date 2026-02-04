#!/usr/bin/env python3
"""
Audio-to-Text Converter using OpenAI Whisper with GPU acceleration.

This script converts French audio files to text using OpenAI Whisper
with mandatory GPU acceleration. The script fails if GPU is not available.

Usage:
    python audio_to_text.py <audio_file> [model_name] [--output <output_file>] [--segments [segments_file]] [--words [words_file]] [--json-sentences [json_file]]

Arguments:
    audio_file: Path to the audio file to transcribe (M4A, MP3, WAV, etc.)
    model_name: Whisper model to use (tiny, base, small, medium, large, large-v2, large-v3)
                Default: large-v3
    --output: Output file path. Default: derives from input filename (e.g., audio.m4a → audio.txt)
    --segments: Save timestamped segments to JSON file. Default: derives from output filename (e.g., audio.txt → audio.segments.json)
    --words: Save word-level timestamps to file. Default: derives from output filename (e.g., audio.txt → audio.words.json)
    --json-sentences: Save as JSON with sentence-level segments. Default: derives from output filename (e.g., audio.txt → audio.json)

Requirements:
    - NVIDIA GPU with CUDA support
    - Python 3.8+
    - Dependencies from requirements.txt
"""

import argparse
import json
import re
import sys
import warnings
from pathlib import Path

import torch
import whisper

# Suppress FutureWarning from torch.load in whisper library
warnings.filterwarnings('ignore', category=FutureWarning, module='whisper')

# Sentence-ending punctuation pattern (compiled once at module level)
SENTENCE_ENDERS = re.compile(r'[.!?…]$')


def check_gpu_availability():
    """Verify that CUDA GPU is available for processing."""
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required but not available")
    return "cuda"


def validate_audio_file(file_path):
    """Validate that the audio file exists and is a supported format."""
    audio_path = Path(file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    supported = {'.m4a', '.mp3', '.wav', '.flac', '.aac', '.ogg'}
    if audio_path.suffix.lower() not in supported:
        raise ValueError(f"Unsupported format: {audio_path.suffix}")

    return audio_path


def load_whisper_model(model_name, device):
    """Load the specified Whisper model on the GPU."""
    try:
        print(f"Loading Whisper model '{model_name}' on GPU...")
        model = whisper.load_model(model_name, device=device)
        print(f"Model '{model_name}' loaded successfully")
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load Whisper model '{model_name}': {e}")


def transcribe_audio(model:whisper.Whisper, audio_path, enable_word_timestamps=False):
    """Transcribe audio file using the loaded Whisper model with French language optimization."""
    try:
        print(f"Transcribing: {audio_path.name}")

        result = model.transcribe(
            str(audio_path),
            language='french',
            task='transcribe',
            temperature=0.0,
            best_of=1,
            beam_size=5,
            patience=1.0,
            length_penalty=1.0,
            suppress_tokens=[-1],
            initial_prompt="",
            condition_on_previous_text=True,
            fp16=True,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            verbose=False,
            word_timestamps=enable_word_timestamps,
        )

        transcribed_text = result['text'].strip()

        if not transcribed_text:
            raise RuntimeError("No text detected in audio")

        detected_language = result.get('language', 'unknown')
        if detected_language != 'french':
            print(f"Warning: Detected language '{detected_language}' differs from expected 'french'")

        return transcribed_text, result['segments'], result

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def save_transcription(text, output_path):
    """Save transcribed text to a file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"Transcription saved: {output_file}")


def save_segments(segments, output_path):
    """Save transcription segments with timestamps to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Format segments for readability
    formatted_segments = [
        {
            'id': seg['id'],
            'start': seg['start'],
            'end': seg['end'],
            'text': seg['text'].strip()
        }
        for seg in segments
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_segments, f, indent=2, ensure_ascii=False)

    print(f"Segments saved: {output_file}")


def save_words(segments, output_path):
    """Save flattened word-level timestamps to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Flatten words from all segments, adding segment_id reference
    all_words = [
        {**word, 'segment_id': seg['id']}
        for seg in segments if 'words' in seg
        for word in seg['words']
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_words, f, indent=2, ensure_ascii=False)

    print(f"Words saved: {output_file}")


def _derive_output_path(arg_value, base_output_path, suffix_modifier=None):
    """
    Derive output path from argument value or base output path.

    Args:
        arg_value: The argument value ('' for auto-derive, path string for explicit, None for not set)
        base_output_path: The base output path to derive from
        suffix_modifier: Optional suffix modifier (e.g., '.segments' for audio.segments.json)
                        If None, just changes extension to .json

    Returns:
        Derived path, or None if arg_value is None
    """
    if arg_value is None:
        return None

    if arg_value == '':
        # Auto-derive from base output path
        output_path = Path(base_output_path)
        if suffix_modifier:
            return output_path.with_stem(output_path.stem + suffix_modifier).with_suffix('.json')
        else:
            return output_path.with_suffix('.json')
    else:
        # Explicit path provided
        return arg_value


def _clean_whisper_spacing(text):
    """
    Fix spacing issues from Whisper's word tokenization.

    Whisper splits contractions and hyphenated words, creating spaces like:
    "c 'est" → "c'est"
    "Maison -Blanche" → "Maison-Blanche"

    Args:
        text: Text with potential spacing issues

    Returns:
        Cleaned text with proper spacing
    """
    # Remove space before apostrophes
    text = re.sub(r"\s+'", "'", text)

    # Remove spaces around hyphens
    text = re.sub(r'\s+-\s+', '-', text)  # "word - word" → "word-word"
    text = re.sub(r'\s+-', '-', text)      # "word -word" → "word-word"
    text = re.sub(r'-\s+', '-', text)      # "word- word" → "word-word"

    return text


def create_sentence_segments(full_text, segments_with_words):
    """
    Split transcription into sentence-level segments with word timestamps.

    Uses word-level timestamps to build sentences by detecting punctuation boundaries.
    This is more reliable than trying to match pre-split sentences to words.

    Args:
        full_text: Complete transcription text (used as fallback if no words available)
        segments_with_words: Whisper segments containing word timestamps

    Returns:
        List of sentence segments with structure:
        [{'id': int, 'start': float, 'end': float, 'text': str}, ...]
    """
    # Flatten all words from Whisper segments
    all_words = []
    for seg in segments_with_words:
        if 'words' in seg:
            all_words.extend(seg['words'])

    # Fallback: if no words available, return single segment with full text
    if not all_words:
        return [{
            'id': 1,
            'start': 0.0,
            'end': 0.0,
            'text': full_text.strip()
        }]

    # Build sentences by iterating through words and detecting punctuation boundaries
    sentence_segments = []
    sentence_id = 1
    current_sentence_words = []
    current_sentence_start = None

    for word_obj in all_words:
        word_text = word_obj['word'].strip()
        if not word_text:
            continue

        # Track start time of first word in sentence
        if current_sentence_start is None:
            current_sentence_start = word_obj['start']

        current_sentence_words.append(word_text)

        # Check if this word ends a sentence
        if SENTENCE_ENDERS.search(word_text):
            # Build sentence text and clean up spacing issues
            sentence_text = ' '.join(current_sentence_words).strip()
            sentence_text = _clean_whisper_spacing(sentence_text)

            segment = {
                'id': sentence_id,
                'start': current_sentence_start,
                'end': word_obj['end'],
                'text': sentence_text
            }
            sentence_segments.append(segment)

            # Reset for next sentence
            sentence_id += 1
            current_sentence_words = []
            current_sentence_start = None

    # Handle remaining words that don't end with punctuation
    if current_sentence_words:
        sentence_text = ' '.join(current_sentence_words).strip()
        sentence_text = _clean_whisper_spacing(sentence_text)
        segment = {
            'id': sentence_id,
            'start': current_sentence_start,
            'end': all_words[-1]['end'],
            'text': sentence_text
        }
        sentence_segments.append(segment)

    return sentence_segments


def save_json_sentences(result, sentence_segments, output_path):
    """
    Save transcription as JSON with sentence-level segments.

    Args:
        result: Full Whisper transcription result (contains language info)
        sentence_segments: List of sentence segments from create_sentence_segments()
        output_path: Path to save JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Calculate duration from last segment's end time
    duration = sentence_segments[-1]['end'] if sentence_segments else 0.0

    # Build output structure
    output_data = {
        'duration': duration,
        'language': result.get('language', 'fr'),
        'segments': sentence_segments
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"JSON sentences saved: {output_file}")


def main():
    """Main entry point for the audio-to-text converter."""
    parser = argparse.ArgumentParser(
        description="Convert audio files to text using OpenAI Whisper with GPU acceleration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'audio_file',
        help='Path to the audio file to transcribe (M4A, MP3, WAV, etc.)'
    )

    parser.add_argument(
        'model',
        nargs='?',
        default='large-v3',
        help='Whisper model to use (default: large-v3). Options: tiny, base, small, medium, large, large-v2, large-v3'
    )

    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output file path. Default: derives from input filename (e.g., audio.m4a → audio.txt)'
    )

    parser.add_argument(
        '--segments', '-s',
        nargs='?',
        const='',
        default=None,
        help='Save transcription segments with timestamps to file. Default: derives from output filename (e.g., audio.txt → audio.segments.json)'
    )

    parser.add_argument(
        '--words', '-w',
        nargs='?',
        const='',
        default=None,
        help='Save word-level timestamps to file. Default: derives from output filename (e.g., audio.txt → audio.words.json)'
    )

    parser.add_argument(
        '--json-sentences', '-j',
        nargs='?',
        const='',
        default=None,
        help='Save transcription as JSON with sentence-level segments. Default: derives from output filename (e.g., audio.txt → audio.json)'
    )

    args = parser.parse_args()

    try:
        # Determine output filename
        if args.output is None:
            audio_path = Path(args.audio_file)
            default_output = audio_path.with_suffix('.txt')
            # Prevent overwriting if input is already .txt
            if default_output == audio_path:
                default_output = audio_path.with_name(audio_path.stem + '.out.txt')
            args.output = default_output

        # Derive output paths for optional outputs
        segments_path = _derive_output_path(args.segments, args.output, '.segments')
        words_path = _derive_output_path(args.words, args.output, '.words')
        json_path = _derive_output_path(args.json_sentences, args.output)

        # Step 1: Verify GPU availability
        print("=== GPU Check ===")
        device = check_gpu_availability()
        print(f"GPU available: {torch.cuda.get_device_name(0)}")

        # Step 2: Validate input file
        print("\n=== Audio File Validation ===")
        audio_path = validate_audio_file(args.audio_file)
        print(f"Audio file validated: {audio_path.name}")

        # Step 3: Load Whisper model on GPU
        print("\n=== Model Loading ===")
        model = load_whisper_model(args.model, device)

        # Step 4: Transcribe audio
        print("\n=== Transcription ===")
        enable_words = args.words is not None or args.json_sentences is not None
        transcribed_text, segments, result = transcribe_audio(model, audio_path, enable_word_timestamps=enable_words)

        # Step 5: Save transcription
        print("\n=== Saving ===")
        save_transcription(transcribed_text, args.output)

        # Save optional outputs if requested
        if segments_path:
            save_segments(segments, segments_path)

        if words_path:
            save_words(segments, words_path)

        if json_path:
            sentence_segments = create_sentence_segments(transcribed_text, segments)
            save_json_sentences(result, sentence_segments, json_path)

        print("\nTranscription completed successfully!")
        return 0

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
