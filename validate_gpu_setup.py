#!/usr/bin/env python3
"""
GPU Setup Validation Script for Audio-to-Text Project

This script validates that the GPU-accelerated Whisper setup is working correctly
with the demo.m4a file for French transcription.

Dependencies verified:
- PyTorch with CUDA support
- OpenAI Whisper
- pydub for audio processing
- demo.m4a file for testing

Usage:
    python validate_gpu_setup.py
"""

import sys
import os
import torch
import whisper
from pydub import AudioSegment


def check_gpu_support():
    """Check if CUDA/GPU support is available."""
    print("=== GPU Support Check ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU device: {torch.cuda.get_device_name(0)}")
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        return True
    else:
        print("❌ CUDA not available - GPU acceleration not possible")
        return False


def check_whisper_installation():
    """Check Whisper installation and available models."""
    print("\n=== Whisper Installation Check ===")
    try:
        models = whisper.available_models()
        print(f"✅ Whisper installed successfully")
        print(f"Available models: {', '.join(models)}")
        return True
    except Exception as e:
        print(f"❌ Whisper installation failed: {e}")
        return False


def check_demo_file():
    """Check if demo.m4a file exists and can be processed."""
    demo_path = "/home/prezbar/dev/audio-to-text2/demo.m4a"
    print(f"\n=== Demo File Check ===")
    print(f"Demo file path: {demo_path}")
    
    if not os.path.exists(demo_path):
        print(f"❌ Demo file not found: {demo_path}")
        return False
    
    try:
        # Test with pydub
        audio = AudioSegment.from_file(demo_path)
        print(f"✅ Audio file loaded successfully")
        print(f"Duration: {len(audio) / 1000:.1f} seconds")
        print(f"Format: {audio.frame_rate}Hz, {audio.channels} channel(s)")
        return True
    except Exception as e:
        print(f"❌ Audio file processing failed: {e}")
        return False


def test_whisper_transcription():
    """Test GPU-accelerated Whisper transcription with demo.m4a."""
    print(f"\n=== Whisper GPU Transcription Test ===")
    
    try:
        # Load base model with GPU support
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model on device: {device}")
        
        model = whisper.load_model("base", device=device)
        print(f"✅ Model loaded on device: {next(model.parameters()).device}")
        
        # Test transcription with demo file
        demo_path = "/home/prezbar/dev/audio-to-text2/demo.m4a"
        print(f"Transcribing {demo_path} with French language setting...")
        
        result = model.transcribe(demo_path, language='fr')
        
        print(f"✅ Transcription successful!")
        print(f"Transcribed text: {result['text']}")
        print(f"Language detected: {result.get('language', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("Audio-to-Text GPU Setup Validation")
    print("=" * 40)
    
    checks = [
        ("GPU Support", check_gpu_support),
        ("Whisper Installation", check_whisper_installation),
        ("Demo File", check_demo_file),
        ("Whisper GPU Transcription", test_whisper_transcription)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n=== Validation Summary ===")
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 All validation checks passed!")
        print(f"GPU-accelerated French audio transcription is ready to use.")
        return 0
    else:
        print(f"\n❌ Some validation checks failed.")
        print(f"Please review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())