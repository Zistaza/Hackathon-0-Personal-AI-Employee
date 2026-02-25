#!/usr/bin/env python3
"""
Integration Orchestrator Status Checker
Verifies system status and displays diagnostics
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def check_file(filepath: Path, description: str) -> bool:
    """Check if file exists"""
    exists = filepath.exists()
    status = "✓" if exists else "✗"
    print(f"  {status} {description}: {filepath.name}")
    return exists


def check_directory(dirpath: Path, description: str) -> bool:
    """Check if directory exists"""
    exists = dirpath.exists()
    status = "✓" if exists else "✗"

    if exists:
        file_count = len(list(dirpath.glob("*.md")))
        print(f"  {status} {description}: {dirpath.name} ({file_count} files)")
    else:
        print(f"  {status} {description}: {dirpath.name} (not found)")

    return exists


def check_state_file(filepath: Path) -> dict:
    """Check processed events state"""
    if not filepath.exists():
        return {"exists": False, "count": 0}

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return {"exists": True, "count": len(data)}
    except Exception as e:
        return {"exists": True, "error": str(e)}


def check_log_file(filepath: Path) -> dict:
    """Check log file"""
    if not filepath.exists():
        return {"exists": False}

    try:
        stats = filepath.stat()
        with open(filepath, 'r') as f:
            lines = f.readlines()

        return {
            "exists": True,
            "size": stats.st_size,
            "lines": len(lines),
            "last_modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"exists": True, "error": str(e)}


def main():
    """Main status check"""
    print("\n" + "=" * 60)
    print("Integration Orchestrator - Status Check")
    print("=" * 60)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    base_dir = Path(__file__).parent.parent.parent

    # Check orchestrator files
    print("📦 Orchestrator Files:")
    orchestrator_dir = Path(__file__).parent
    check_file(orchestrator_dir / "index.py", "Main script")
    check_file(orchestrator_dir / "requirements.txt", "Dependencies")
    check_file(orchestrator_dir / "README.md", "Documentation")
    check_file(orchestrator_dir / "setup.sh", "Setup script")
    check_file(orchestrator_dir / "run.sh", "Runner script")

    # Check monitored directories
    print("\n📁 Monitored Directories:")
    check_directory(base_dir / "Inbox", "Inbox")
    check_directory(base_dir / "Needs_Action", "Needs_Action")
    check_directory(base_dir / "Pending_Approval", "Pending_Approval")
    check_directory(base_dir / "Done", "Done")
    check_directory(base_dir / "Logs", "Logs")

    # Check skills
    print("\n🔧 Required Skills:")
    skills_dir = base_dir / "Skills"
    check_directory(skills_dir / "process_needs_action", "process_needs_action")
    check_directory(skills_dir / "linkedin_post_skill", "linkedin_post_skill")

    # Check state
    print("\n💾 State Management:")
    state_file = orchestrator_dir / "processed_events.json"
    state = check_state_file(state_file)

    if state["exists"]:
        if "error" in state:
            print(f"  ✗ State file: Error - {state['error']}")
        else:
            print(f"  ✓ State file: {state['count']} processed event(s)")
    else:
        print(f"  ✗ State file: Not found (will be created on first run)")

    # Check logs
    print("\n📝 Logs:")
    log_file = base_dir / "Logs" / "integration_orchestrator.log"
    log = check_log_file(log_file)

    if log["exists"]:
        if "error" in log:
            print(f"  ✗ Log file: Error - {log['error']}")
        else:
            print(f"  ✓ Log file: {log['size']} bytes, {log['lines']} lines")
            print(f"    Last modified: {log['last_modified']}")

            # Show last 5 lines
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"\n    Last 5 log entries:")
                        for line in lines[-5:]:
                            print(f"    {line.rstrip()}")
            except Exception:
                pass
    else:
        print(f"  ✗ Log file: Not found (will be created on first run)")

    # Check if running
    print("\n🚀 Process Status:")
    try:
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "integration_orchestrator"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"  ✓ Orchestrator is running (PID: {', '.join(pids)})")
        else:
            print(f"  ✗ Orchestrator is not running")
            print(f"    Start with: python3 index.py")
    except Exception:
        print(f"  ? Unable to check process status")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    print("\nTo start orchestrator:")
    print("  python3 index.py")

    print("\nTo view logs:")
    print("  tail -f ../../Logs/integration_orchestrator.log")

    print("\nTo test system:")
    print("  Create a test file in Needs_Action/")
    print("  Watch logs for processing")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
