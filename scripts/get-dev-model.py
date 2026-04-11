#!/usr/bin/env python3
"""Download development test model for LLMLaunchpad.

This script downloads the Phi-3 Mini Q4 model for development testing.
The model is ~1.8GB and suitable for testing the LLMLaunchpad stack.

Exit codes:
    0 - Success (downloaded or already exists)
    1 - Error (network, disk space, etc.)
    2 - Already exists (not an error, but indicates no action taken)
"""

import os
import sys
import urllib.request
from pathlib import Path

MODEL_URL = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
MODEL_NAME = "Phi-3-mini-4k-instruct-q4.gguf"
EXPECTED_SIZE = 1.8 * 1024 * 1024 * 1024


def get_dev_models_dir() -> Path:
    """Get the dev models directory path."""
    home = Path.home()
    return home / ".llmlaunchpad" / "models" / "dev"


def model_exists() -> tuple[bool, Path]:
    """Check if the model already exists."""
    dev_dir = get_dev_models_dir()
    model_path = dev_dir / MODEL_NAME
    return model_path.exists(), model_path


class DownloadProgress:
    def __init__(self, expected_size: int):
        self.expected_size = expected_size
        self.downloaded = 0
        self.last_percent = -1
    
    def __call__(self, block_num: int, block_size: int, total_size: int):
        self.downloaded = block_num * block_size
        size = total_size if total_size > 0 else self.expected_size
        
        if size > 0:
            percent = min(100, int(self.downloaded * 100 / size))
            
            if percent != self.last_percent:
                self.last_percent = percent
                downloaded_mb = self.downloaded / (1024 * 1024)
                size_mb = size / (1024 * 1024)
                print(f"\r  Downloading: {percent:3d}% ({downloaded_mb:.1f} / {size_mb:.1f} MB)", 
                      end="", flush=True)


def download_model(destination: Path) -> bool:
    progress = DownloadProgress(EXPECTED_SIZE)
    
    try:
        req = urllib.request.Request(
            MODEL_URL,
            headers={"User-Agent": "LLMLaunchpad/1.0"}
        )
        
        urllib.request.urlretrieve(req, destination, reporthook=progress)
        print()
        return True
        
    except urllib.error.HTTPError as e:
        print(f"\n  Error: HTTP {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"\n  Error: Network error - {e.reason}")
        return False
    except Exception as e:
        print(f"\n  Error: {e}")
        return False


def verify_download(path: Path) -> bool:
    if not path.exists():
        print("  Error: File not found after download")
        return False
    
    actual_size = path.stat().st_size
    
    if actual_size < 1024 * 1024 * 1024:
        print(f"  Error: File too small ({actual_size / (1024*1024):.1f} MB)")
        return False
    
    size_diff = abs(actual_size - EXPECTED_SIZE) / EXPECTED_SIZE
    if size_diff > 0.1:
        print(f"  Warning: File size differs from expected")
        print(f"    Expected: {EXPECTED_SIZE / (1024*1024*1024):.1f} GB")
        print(f"    Actual:   {actual_size / (1024*1024*1024):.1f} GB")
    
    return True


def main() -> int:
    print("=" * 50)
    print("LLMLaunchpad - Development Model Download")
    print("=" * 50)
    print()
    
    exists, model_path = model_exists()
    if exists:
        print(f"Model already exists:")
        print(f"  {model_path}")
        print()
        print(f"Size: {model_path.stat().st_size / (1024*1024*1024):.2f} GB")
        return 2
    
    dev_dir = get_dev_models_dir()
    try:
        dev_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dev_dir}")
    except OSError as e:
        print(f"Error: Failed to create directory: {e}")
        return 1
    
    print(f"\nDownloading: {MODEL_NAME}")
    print(f"From: {MODEL_URL}")
    print(f"To: {model_path}")
    print()
    
    if not download_model(model_path):
        if model_path.exists():
            try:
                model_path.unlink()
            except OSError:
                pass
        return 1
    
    print("\nVerifying download...")
    if not verify_download(model_path):
        if model_path.exists():
            try:
                model_path.unlink()
            except OSError:
                pass
        return 1
    
    actual_size = model_path.stat().st_size
    print(f"  File size: {actual_size / (1024*1024*1024):.2f} GB")
    print()
    print("=" * 50)
    print("Download complete!")
    print("=" * 50)
    print()
    print(f"Model saved to:")
    print(f"  {model_path}")
    print()
    print("You can now use this model in LLMLaunchpad:")
    print("  1. Start the app: npm run dev")
    print("  2. Select 'Phi-3-mini-4k-instruct-q4.gguf' from the model list")
    print("  3. Click 'Start' to launch llama.cpp")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
