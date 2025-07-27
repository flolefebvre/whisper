#!/usr/bin/env python3
"""
Audio-to-Text Project Setup Verification Script
Verifies that the development environment is properly configured.
"""

import sys
import os
from pathlib import Path

def verify_python_version():
    """Verify Python version is 3.8 or higher."""
    version = sys.version_info
    required = (3, 8)
    
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= required:
        print("✅ Python version requirement satisfied")
        return True
    else:
        print(f"❌ Python version {required[0]}.{required[1]}+ required")
        return False

def verify_virtual_environment():
    """Verify that we're running in a virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("✅ Virtual environment active")
        print(f"   Virtual env path: {sys.prefix}")
        return True
    else:
        print("⚠️  Not running in virtual environment")
        return False

def verify_project_structure():
    """Verify project directory structure."""
    project_root = Path(__file__).parent
    required_dirs = ['src', 'tests', 'docs', 'samples']
    
    print("Project directory structure:")
    all_present = True
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"❌ {dir_name}/ directory missing")
            all_present = False
    
    # Check for important files
    important_files = ['.gitignore', 'tasks.md']
    for file_name in important_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✅ {file_name} exists")
        else:
            print(f"❌ {file_name} missing")
            all_present = False
    
    return all_present

def main():
    """Run all verification checks."""
    print("🔍 Audio-to-Text Project Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Python Version", verify_python_version),
        ("Virtual Environment", verify_virtual_environment),
        ("Project Structure", verify_project_structure)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        passed = check_func()
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Environment setup verification PASSED!")
        print("Ready to proceed with Task 1.2 - Dependencies Configuration")
    else:
        print("❌ Environment setup verification FAILED!")
        print("Please address the issues above before proceeding.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)