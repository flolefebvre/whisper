#!/usr/bin/env python3
"""
Audio-to-Text Converter using OpenAI Whisper with GPU acceleration.

This script converts French M4A audio files to text using OpenAI Whisper
with mandatory GPU acceleration. The script fails if GPU is not available.

Usage:
    python audio_to_text.py <audio_file> [model_name] [--output <output_file>] [--format <txt|json>]

Arguments:
    audio_file: Path to the M4A audio file to transcribe
    model_name: Whisper model to use (tiny, base, small, medium, large, large-v2, large-v3)
                Default: base
    --output: Optional output file path. If not specified, prints to console.

Requirements:
    - NVIDIA GPU with CUDA support
    - Python 3.8+
    - Dependencies from requirements.txt
"""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

import torch
import whisper
from pydub import AudioSegment


def check_gpu_availability():
    """
    Verify that CUDA GPU is available for processing.
    
    Returns:
        bool: True if GPU is available, False otherwise.
        
    Raises:
        RuntimeError: If CUDA is not available with detailed error message.
    """
    if not torch.cuda.is_available():
        raise RuntimeError(
            "GPU acceleration required but CUDA is not available. "
            "Please ensure NVIDIA GPU drivers and CUDA toolkit are properly installed."
        )
    
    device_count = torch.cuda.device_count()
    if device_count == 0:
        raise RuntimeError(
            "No CUDA devices detected. "
            "Please check your GPU hardware and driver installation."
        )
    
    # Get GPU information
    device_name = torch.cuda.get_device_name(0)
    memory_total = torch.cuda.get_device_properties(0).total_memory
    memory_gb = memory_total / (1024**3)
    
    print(f"GPU detected: {device_name}")
    print(f"GPU memory: {memory_gb:.1f} GB")
    print(f"CUDA version: {torch.version.cuda}")
    
    return True


def validate_audio_file(file_path):
    """
    Validate that the audio file exists and is readable.
    
    Args:
        file_path (str): Path to the audio file.
        
    Returns:
        Path: Validated Path object for the audio file.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file is not a supported audio format.
    """
    audio_path = Path(file_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    if not audio_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Check file extension
    supported_extensions = {'.m4a', '.mp3', '.wav', '.flac', '.aac', '.ogg'}
    if audio_path.suffix.lower() not in supported_extensions:
        raise ValueError(
            f"Unsupported audio format: {audio_path.suffix}. "
            f"Supported formats: {', '.join(supported_extensions)}"
        )
    
    # Try to load audio file to verify it's valid
    try:
        # Quick validation by loading just the first second
        audio = AudioSegment.from_file(str(audio_path))
        duration = len(audio) / 1000.0  # Convert to seconds
        print(f"Audio file validated: {audio_path.name}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Sample rate: {audio.frame_rate} Hz")
        print(f"Channels: {audio.channels}")
    except Exception as e:
        raise ValueError(f"Invalid audio file: {e}")
    
    return audio_path


def validate_whisper_model(model_name):
    """
    Validate that the specified Whisper model name is supported.
    
    Args:
        model_name (str): Name of the Whisper model.
        
    Returns:
        str: Validated model name.
        
    Raises:
        ValueError: If model name is not supported.
    """
    available_models = {
        'tiny', 'base', 'small', 'medium', 
        'large', 'large-v2', 'large-v3'
    }
    
    if model_name not in available_models:
        raise ValueError(
            f"Unsupported model: {model_name}. "
            f"Available models: {', '.join(sorted(available_models))}"
        )
    
    return model_name


def load_whisper_model(model_name, device):
    """
    Load the specified Whisper model on the GPU.
    
    Args:
        model_name (str): Name of the Whisper model to load.
        device (str): Device to load the model on ('cuda').
        
    Returns:
        whisper.Whisper: Loaded Whisper model.
        
    Raises:
        RuntimeError: If model loading fails.
    """
    try:
        print(f"Loading Whisper model '{model_name}' on GPU...")
        model = whisper.load_model(model_name, device=device)
        print(f"Model '{model_name}' loaded successfully on {device}")
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load Whisper model '{model_name}': {e}")


def transcribe_audio(model, audio_path):
    """
    Transcribe audio file using the loaded Whisper model with French language optimization.
    
    Args:
        model: Loaded Whisper model.
        audio_path (Path): Path to the audio file.
        
    Returns:
        tuple: (transcribed_text, detected_language) for validation.
        
    Raises:
        RuntimeError: If transcription fails.
    """
    try:
        print(f"Transcribing audio file: {audio_path.name}")
        print("Processing with French language optimization...")
        
        # Transcribe with French language optimization
        result = model.transcribe(
            str(audio_path),
            language='french',      # Set language to French for optimal recognition
            task='transcribe',      # Explicit transcription task (not translation)
            temperature=0.0,        # Use deterministic output for consistency
            best_of=1,             # Use best result (no sampling)
            beam_size=5,           # Use beam search for better accuracy
            patience=1.0,          # Patience for beam search
            length_penalty=1.0,    # No length penalty
            suppress_tokens=[-1],  # Suppress only the end-of-text token
            initial_prompt="",     # No initial prompt to let the model detect French naturally
            condition_on_previous_text=True,  # Use context from previous segments
            fp16=True,             # Use half precision for faster GPU processing
            compression_ratio_threshold=2.4,  # Standard threshold for text consistency
            logprob_threshold=-1.0,            # Standard threshold for confidence
            no_speech_threshold=0.6,           # Threshold for detecting speech vs silence
            verbose=False          # Reduce console output during processing
        )
        
        # Extract the transcribed text
        transcribed_text = result['text'].strip()
        
        if not transcribed_text:
            raise RuntimeError("Transcription completed but no text was detected in the audio")
        
        # Extract detected language for validation
        detected_language = result.get('language', 'unknown')
        print(f"Detected language: {detected_language}")
        if detected_language != 'french':
            print(f"Warning: Detected language '{detected_language}' differs from expected 'french'")
        
        print("French transcription completed successfully!")
        return transcribed_text, detected_language
        
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def validate_french_transcription(text, detected_language=None):
    """
    Validate and analyze French transcription quality.
    
    Args:
        text (str): Transcribed text to analyze.
        detected_language (str): Language detected by Whisper.
        
    Returns:
        dict: Analysis results including quality indicators.
    """
    analysis = {
        'text_length': len(text),
        'word_count': len(text.split()),
        'has_french_chars': False,
        'common_french_words': 0,
        'quality_score': 'unknown'
    }
    
    # Check for French-specific characters
    french_chars = 'àâäéèêëîïôöùûüÿçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇ'
    analysis['has_french_chars'] = any(char in text for char in french_chars)
    
    # Check for common French words (basic validation)
    common_french_words = [
        'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une',
        'et', 'ou', 'à', 'avec', 'pour', 'dans', 'sur',
        'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
        'est', 'sont', 'était', 'être', 'avoir', 'faire',
        'bonjour', 'merci', 'oui', 'non', 'bien', 'très',
        'français', 'france', 'parler', 'parle'
    ]
    
    text_lower = text.lower()
    found_words = [word for word in common_french_words if word in text_lower]
    analysis['common_french_words'] = len(found_words)
    
    # Simple quality assessment
    if analysis['word_count'] == 0:
        analysis['quality_score'] = 'empty'
    elif detected_language and detected_language != 'french':
        analysis['quality_score'] = f'language_mismatch_{detected_language}'
    elif analysis['common_french_words'] >= 2 or analysis['has_french_chars']:
        analysis['quality_score'] = 'good_french_indicators'
    elif analysis['word_count'] >= 3:
        analysis['quality_score'] = 'acceptable_length'
    else:
        analysis['quality_score'] = 'needs_review'
    
    return analysis


def save_transcription(text, output_path, output_format='txt', metadata=None):
    """
    Save transcribed text to a file in the specified format.
    
    Args:
        text (str): Transcribed text to save.
        output_path (str): Path where to save the file.
        output_format (str): Output format ('txt' or 'json').
        metadata (dict): Optional metadata to include in JSON format.
        
    Raises:
        IOError: If file writing fails.
        PermissionError: If lacking write permissions to the output path.
        ValueError: If output format is not supported.
    """
    if output_format not in ['txt', 'json']:
        raise ValueError(f"Unsupported output format: {output_format}. Supported formats: txt, json")
    
    try:
        output_file = Path(output_path)
        
        # Create output directory if it doesn't exist
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionError(f"No permission to create directory: {output_file.parent}")
        
        # Check write permissions before attempting to write
        if output_file.exists() and not os.access(output_file, os.W_OK):
            raise PermissionError(f"No write permission for existing file: {output_file}")
        elif not output_file.exists() and not os.access(output_file.parent, os.W_OK):
            raise PermissionError(f"No write permission for directory: {output_file.parent}")
        
        # Write content based on format
        if output_format == 'txt':
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
        elif output_format == 'json':
            # Ensure output file has .json extension for JSON format
            if not output_file.suffix.lower() == '.json':
                output_file = output_file.with_suffix('.json')
            
            json_data = {
                'transcription': text,
                'metadata': metadata or {}
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"Transcription saved to: {output_file.absolute()} (format: {output_format})")
        
    except PermissionError:
        raise  # Re-raise permission errors with original message
    except FileNotFoundError as e:
        raise IOError(f"Invalid output path: {e}")
    except Exception as e:
        raise IOError(f"Failed to save transcription: {e}")


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
        default='base',
        help='Whisper model to use (default: base). Options: tiny, base, small, medium, large, large-v2, large-v3'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path for transcription. If not specified, prints to console.'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['txt', 'json'],
        default='txt',
        help='Output format for transcription (default: txt). JSON format includes metadata.'
    )
    
    args = parser.parse_args()
    
    try:
        # Step 1: Verify GPU availability (MANDATORY)
        print("=== GPU Environment Check ===")
        check_gpu_availability()
        device = "cuda"
        
        # Step 2: Validate input file
        print("\n=== Audio File Validation ===")
        audio_path = validate_audio_file(args.audio_file)
        
        # Step 3: Validate model name
        print("\n=== Model Validation ===")
        model_name = validate_whisper_model(args.model)
        
        # Step 4: Load Whisper model on GPU
        print("\n=== Model Loading ===")
        model = load_whisper_model(model_name, device)
        
        # Step 5: Transcribe audio
        print("\n=== Transcription ===")
        transcribed_text, detected_language = transcribe_audio(model, audio_path)
        
        # Step 6: Validate French transcription quality
        print("\n=== French Language Validation ===")
        analysis = validate_french_transcription(transcribed_text, detected_language)
        print(f"Word count: {analysis['word_count']}")
        print(f"Text length: {analysis['text_length']} characters")
        print(f"French characters detected: {'Yes' if analysis['has_french_chars'] else 'No'}")
        print(f"Common French words found: {analysis['common_french_words']}")
        print(f"Quality assessment: {analysis['quality_score']}")
        
        # Step 7: Output results
        print("\n=== Results ===")
        if args.output:
            # Prepare metadata for JSON format
            metadata = {
                'audio_file': str(audio_path.absolute()),
                'model_used': model_name,
                'detected_language': detected_language,
                'duration_seconds': len(AudioSegment.from_file(str(audio_path))) / 1000.0,
                'word_count': analysis['word_count'],
                'text_length': analysis['text_length'],
                'quality_score': analysis['quality_score']
            }
            save_transcription(transcribed_text, args.output, args.format, metadata)
        else:
            print("Transcribed text:")
            print("-" * 50)
            print(transcribed_text)
            print("-" * 50)
            if args.format == 'json':
                print("\nNote: JSON format only available when using --output option.")
        
        print("\nFrench audio transcription completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        
        # Print full traceback in debug mode
        if os.environ.get('DEBUG'):
            print("\nFull traceback:", file=sys.stderr)
            traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())