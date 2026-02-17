#!/usr/bin/env python3
"""
Safe JSON Log Appender for Bronze Tier AI Employee
Appends log entries to daily JSON log files with safety features
"""

import json
import shutil
import sys
from pathlib import Path
from datetime import datetime


def append_log_entry(log_file, new_entry):
    """
    Safely append a log entry to a JSON log file.

    Features:
    - Creates file if missing
    - Handles corrupted JSON gracefully
    - Atomic writes with backup
    - Validates JSON before replacing
    """
    log_path = Path(log_file)
    temp_path = Path(str(log_file) + ".tmp")
    backup_path = Path(str(log_file) + ".backup")

    # Create logs directory if missing
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Read existing entries
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                    if not content:
                        log_entries = []
                    else:
                        log_entries = json.loads(content)

                        if not isinstance(log_entries, list):
                            raise ValueError("Log file is not a JSON array")

            except (json.JSONDecodeError, ValueError) as e:
                # Corrupted JSON - backup and start fresh
                print(f"⚠ Warning: Corrupted log file detected: {e}")
                corrupted_backup = Path(str(log_file) + f".corrupted.{int(datetime.now().timestamp())}")
                shutil.copy2(log_path, corrupted_backup)
                print(f"✓ Backup created: {corrupted_backup}")
                log_entries = []
        else:
            # File doesn't exist
            log_entries = []

        # Step 2: Append new entry
        log_entries.append(new_entry)

        # Step 3: Write to temporary file
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(log_entries, f, indent=2, ensure_ascii=False)

        # Step 4: Validate temp file
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Will raise exception if invalid

        # Step 5: Create backup of existing file
        if log_path.exists():
            shutil.copy2(log_path, backup_path)

        # Step 6: Atomically replace old file
        shutil.move(str(temp_path), str(log_path))

        print(f"✓ Log entry written to {log_path}")
        print(f"✓ Total entries: {len(log_entries)}")
        return True

    except Exception as e:
        print(f"✗ Error writing log entry: {e}")

        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()

        # Restore from backup if needed
        if backup_path.exists() and not log_path.exists():
            shutil.copy2(backup_path, log_path)
            print("✓ Restored log file from backup")

        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 append_log.py <log_file> <json_entry>")
        print("")
        print("Example:")
        print('  python3 append_log.py Logs/2026-02-18.json \'{"timestamp":"2026-02-18T10:00:00Z","action":"test"}\'')
        sys.exit(1)

    log_file = sys.argv[1]

    # Parse JSON entry from command line or stdin
    if sys.argv[2] == '-':
        # Read from stdin
        new_entry = json.load(sys.stdin)
    else:
        # Parse from argument
        try:
            new_entry = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            print(f"✗ Error: Invalid JSON entry: {e}")
            sys.exit(1)

    # Append the entry
    success = append_log_entry(log_file, new_entry)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
