#!/usr/bin/env python
"""Test script for huggems conda package."""

import sys
import subprocess


def run_command(cmd, description):
    """Run a command and check result."""
    print(f"\nTesting: {description}")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ {description} - PASSED")
        return True
    else:
        print(f"✗ {description} - FAILED")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False


def main():
    """Run all tests."""
    tests = [
        (["huggems", "--help"], "huggems --help"),
        (["huggems", "presence", "--help"], "huggems presence --help"),
        (["huggems", "markers", "--help"], "huggems markers --help"),
    ]

    all_passed = True
    for cmd, desc in tests:
        if not run_command(cmd, desc):
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
