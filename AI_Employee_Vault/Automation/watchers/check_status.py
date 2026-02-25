#!/usr/bin/env python3
"""
Watcher Status Checker
Checks status of running watchers and displays statistics
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def check_tracking_file(name: str) -> dict:
    """Check tracking file for a watcher"""
    tracking_file = Path(__file__).parent / f"{name}_processed.json"

    if not tracking_file.exists():
        return {
            "exists": False,
            "count": 0,
            "last_modified": None
        }

    try:
        with open(tracking_file, 'r') as f:
            data = json.load(f)

        stats = tracking_file.stat()
        last_modified = datetime.fromtimestamp(stats.st_mtime)

        return {
            "exists": True,
            "count": len(data),
            "last_modified": last_modified.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "exists": True,
            "count": 0,
            "error": str(e)
        }


def check_log_file(name: str) -> dict:
    """Check log file for a watcher"""
    logs_dir = Path(__file__).parent.parent.parent / "Logs"
    log_file = logs_dir / f"{name}_watcher.log"

    if not log_file.exists():
        return {
            "exists": False,
            "size": 0,
            "last_modified": None,
            "last_lines": []
        }

    try:
        stats = log_file.stat()
        last_modified = datetime.fromtimestamp(stats.st_mtime)

        # Read last 5 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            last_lines = [line.strip() for line in lines[-5:]]

        return {
            "exists": True,
            "size": stats.st_size,
            "last_modified": last_modified.strftime("%Y-%m-%d %H:%M:%S"),
            "last_lines": last_lines
        }
    except Exception as e:
        return {
            "exists": True,
            "error": str(e)
        }


def check_session(name: str, session_type: str) -> dict:
    """Check session directory or file"""
    if session_type == "dir":
        session_path = Path(__file__).parent / f"{name}_session"
        if not session_path.exists():
            return {"exists": False}
        return {
            "exists": True,
            "files": len(list(session_path.glob("*")))
        }
    else:  # file
        session_path = Path(__file__).parent / f"{name}_token.pickle"
        if not session_path.exists():
            return {"exists": False}
        stats = session_path.stat()
        return {
            "exists": True,
            "size": stats.st_size,
            "last_modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        }


def print_watcher_status(name: str, display_name: str, session_type: str):
    """Print status for a single watcher"""
    print(f"\n{'=' * 60}")
    print(f"{display_name} Watcher")
    print('=' * 60)

    # Check tracking file
    tracking = check_tracking_file(name)
    print(f"\n📊 Tracking File:")
    if tracking["exists"]:
        print(f"   ✓ Exists: {name}_processed.json")
        print(f"   ✓ Processed items: {tracking['count']}")
        if tracking.get("last_modified"):
            print(f"   ✓ Last updated: {tracking['last_modified']}")
        if tracking.get("error"):
            print(f"   ✗ Error: {tracking['error']}")
    else:
        print(f"   ✗ Not found (watcher not run yet)")

    # Check session
    session = check_session(name, session_type)
    print(f"\n🔐 Session:")
    if session["exists"]:
        if session_type == "dir":
            print(f"   ✓ Session directory exists")
            print(f"   ✓ Files: {session['files']}")
        else:
            print(f"   ✓ Token file exists")
            print(f"   ✓ Size: {session['size']} bytes")
            print(f"   ✓ Last modified: {session['last_modified']}")
    else:
        print(f"   ✗ Not found (authentication required)")

    # Check log file
    log = check_log_file(name)
    print(f"\n📝 Log File:")
    if log["exists"]:
        print(f"   ✓ Exists: {name}_watcher.log")
        print(f"   ✓ Size: {log['size']} bytes")
        if log.get("last_modified"):
            print(f"   ✓ Last updated: {log['last_modified']}")
        if log.get("last_lines"):
            print(f"\n   Last 5 log entries:")
            for line in log["last_lines"]:
                print(f"   {line}")
        if log.get("error"):
            print(f"   ✗ Error: {log['error']}")
    else:
        print(f"   ✗ Not found (watcher not run yet)")


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("AI Employee Watchers - Status Check")
    print("=" * 60)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check each watcher
    print_watcher_status("gmail", "Gmail", "file")
    print_watcher_status("whatsapp", "WhatsApp", "dir")
    print_watcher_status("linkedin", "LinkedIn", "dir")

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print('=' * 60)

    needs_action_dir = Path(__file__).parent.parent.parent / "Needs_Action"
    if needs_action_dir.exists():
        files = list(needs_action_dir.glob("*.md"))
        print(f"\n📁 Needs_Action: {len(files)} file(s)")
    else:
        print(f"\n📁 Needs_Action: Directory not found")

    print("\n" + "=" * 60)
    print()


if __name__ == "__main__":
    main()
