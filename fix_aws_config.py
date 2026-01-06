#!/usr/bin/env python3
"""
Fix AWS config file by removing malformed eb-cli profile.
"""
import os
import shutil
from pathlib import Path

config_path = Path.home() / ".aws" / "config"

if not config_path.exists():
    print(f"Config file not found: {config_path}")
    print("Run 'aws configure' to create it.")
    exit(1)

# Backup
backup_path = config_path.with_suffix(f".config.backup.{os.getpid()}")
shutil.copy(config_path, backup_path)
print(f"✓ Backed up config to: {backup_path}")

# Read and fix
with open(config_path, 'r') as f:
    lines = f.readlines()

# Remove the malformed [profile eb-cli] section
fixed_lines = []
skip_section = False
in_eb_cli_section = False

for i, line in enumerate(lines):
    # Detect start of eb-cli profile
    if line.strip() == '[profile eb-cli]':
        in_eb_cli_section = True
        skip_section = True
        print("  Removing malformed [profile eb-cli] section...")
        continue

    # Detect end of section (next [section] or end of file)
    if skip_section:
        if line.strip().startswith('[') and not line.strip().startswith('[profile eb-cli]'):
            skip_section = False
            fixed_lines.append(line)
        elif line.strip() == '' and i < len(lines) - 1:
            # Check if next line starts a new section
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('['):
                skip_section = False
        # Skip lines in the malformed section
        continue

    fixed_lines.append(line)

# Write fixed content
with open(config_path, 'w') as f:
    f.writelines(fixed_lines)

print(f"✓ Fixed config file: {config_path}")
print("\nCurrent config:")
print("-" * 50)
with open(config_path, 'r') as f:
    print(f.read())
print("-" * 50)
print("\nNext steps:")
print("1. Verify AWS credentials: aws sts get-caller-identity")
print("2. If that works, try: eb init")
