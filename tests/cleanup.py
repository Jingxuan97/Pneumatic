#!/usr/bin/env python3
"""
Manual cleanup script for test artifacts.
Run this if pytest cleanup doesn't work properly.
"""
import os
import shutil
import glob

def cleanup_test_files():
    """Remove all test-related files and directories."""

    # Test database files
    test_db_patterns = [
        "test.db",
        "test.sqlite",
        "test.sqlite3",
        "pytest.db",
        "pytest.sqlite",
        "*.db-journal",
        "*.sqlite-journal",
    ]

    for pattern in test_db_patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"Removed: {file}")
            except Exception as e:
                print(f"Could not remove {file}: {e}")

    # Cache directories
    cache_dirs = [
        "tests/__pycache__",
        "__pycache__",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".tox",
    ]

    for cache_dir in cache_dirs:
        try:
            if os.path.exists(cache_dir):
                if os.path.isdir(cache_dir):
                    shutil.rmtree(cache_dir)
                    print(f"Removed directory: {cache_dir}")
                else:
                    os.remove(cache_dir)
                    print(f"Removed file: {cache_dir}")
        except Exception as e:
            print(f"Could not remove {cache_dir}: {e}")

    # Python cache files
    for root, dirs, files in os.walk("."):
        # Skip virtual environments
        if ".venv" in root or "venv" in root or "__pycache__" in root:
            continue

        for file in files:
            if file.endswith((".pyc", ".pyo", ".pyd")):
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    print(f"Removed: {filepath}")
                except Exception:
                    pass

    print("\nCleanup complete!")

if __name__ == "__main__":
    cleanup_test_files()
