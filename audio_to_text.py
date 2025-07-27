#!/usr/bin/env python3
"""
Audio-to-Text Converter using OpenAI Whisper with GPU acceleration.

This script converts French M4A audio files to text using OpenAI Whisper
with mandatory GPU acceleration. The script fails if GPU is not available.

Usage:
    python audio_to_text.py <audio_file> [model_name] [--output <output_file>]

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
    Transcribe audio file using the loaded Whisper model.
    
    Args:
        model: Loaded Whisper model.
        audio_path (Path): Path to the audio file.
        
    Returns:
        str: Transcribed text.
        
    Raises:
        RuntimeError: If transcription fails.
    """
    try:
        print(f"Transcribing audio file: {audio_path.name}")
        print("Processing... (this may take a few moments)")
        
        # Transcribe with French language hint for better accuracy
        result = model.transcribe(
            str(audio_path),
            language='french',  # Optimize for French audio
            verbose=False       # Reduce console output during processing
        )
        
        # Extract the transcribed text
        transcribed_text = result['text'].strip()
        
        if not transcribed_text:
            raise RuntimeError("Transcription completed but no text was detected in the audio")
        
        print("Transcription completed successfully!")
        return transcribed_text
        
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def save_transcription(text, output_path):
    """
    Save transcribed text to a file.
    
    Args:
        text (str): Transcribed text to save.
        output_path (str): Path where to save the text file.
        
    Raises:
        IOError: If file writing fails.
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Transcription saved to: {output_file.absolute()}")
        
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
        transcribed_text = transcribe_audio(model, audio_path)
        
        # Step 6: Output results
        print("\n=== Results ===")
        if args.output:
            save_transcription(transcribed_text, args.output)
        else:
            print("Transcribed text:")
            print("-" * 50)
            print(transcribed_text)
            print("-" * 50)
        
        print("\nTranscription completed successfully!")
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