#!/usr/bin/env python3
"""
Audio-to-Text Converter using OpenAI Whisper with GPU acceleration.

This script converts French audio files to text using OpenAI Whisper
with mandatory GPU acceleration. The script fails if GPU is not available.

Usage:
    python audio_to_text.py <audio_file> [model_name] [--output <output_file>] [--segments [segments_file]] [--words [words_file]]

Arguments:
    audio_file: Path to the audio file to transcribe (M4A, MP3, WAV, etc.)
    model_name: Whisper model to use (tiny, base, small, medium, large, large-v2, large-v3)
                Default: large-v3
    --output: Output file path. Default: derives from input filename (e.g., audio.m4a → audio.txt)
    --segments: Save timestamped segments to JSON file. Default: derives from output filename (e.g., audio.txt → audio.segments.json)
    --words: Save word-level timestamps to file. Default: derives from output filename (e.g., audio.txt → audio.words.json)

Requirements:
    - NVIDIA GPU with CUDA support
    - Python 3.8+
    - Dependencies from requirements.txt
"""

import argparse
import sys
from pathlib import Path

import torch
import whisper


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

        return transcribed_text, result['segments']

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
    import json
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
    import json
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

        # Determine segments output filename if segments flag is present
        if args.segments is not None:
            if args.segments == '':
                # Derive from output filename
                output_path = Path(args.output)
                segments_path = output_path.with_stem(output_path.stem + '.segments').with_suffix('.json')
            else:
                segments_path = args.segments

        # Determine words output filename if words flag is present
        if args.words is not None:
            if args.words == '':
                # Derive from output filename
                output_path = Path(args.output)
                words_path = output_path.with_stem(output_path.stem + '.words').with_suffix('.json')
            else:
                words_path = args.words

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
        enable_words = args.words is not None
        transcribed_text, segments = transcribe_audio(model, audio_path, enable_word_timestamps=enable_words)

        # Step 5: Save transcription
        print("\n=== Saving ===")
        save_transcription(transcribed_text, args.output)

        # Save segments if requested
        if args.segments is not None:
            save_segments(segments, segments_path)

        # Save words if requested
        if args.words is not None:
            save_words(segments, words_path)

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
