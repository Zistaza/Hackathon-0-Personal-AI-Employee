#!/usr/bin/env python3
"""
Test Email Approval Workflow
Demonstrates the Human-in-the-Loop email approval system
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add orchestrator to path
sys.path.append(str(Path(__file__).parent))
from create_email_approval import create_email_approval


def test_workflow():
    """Test the complete email approval workflow"""

    print("=" * 60)
    print("Email Approval Workflow Test")
    print("=" * 60)
    print()

    # Step 1: Create approval request
    print("Step 1: Creating email approval request...")
    print("-" * 60)

    to = "zinatyamin@gmail.com"
    subject = "Test Email - Human-in-the-Loop Workflow"
    body = """Hello!

This is a test email from the enhanced AI Employee system.

The new Human-in-the-Loop workflow ensures that:
✓ No email is sent automatically
✓ Every email requires explicit human approval
✓ Duplicate emails are prevented
✓ All actions are logged

To approve this email:
1. Check /Pending_Approval/email/ for this approval request
2. Review the email details
3. Move the file to /Approved/
4. The orchestrator will send the email automatically

To reject this email:
1. Move the file to /Rejected/ instead
2. No email will be sent

Best regards,
AI Employee System
"""

    filepath = create_email_approval(to, subject, body)
    print()

    # Step 2: Instructions for human
    print("Step 2: Human Review Required")
    print("-" * 60)
    print(f"✓ Approval request created: {filepath.name}")
    print()
    print("Next steps:")
    print("  1. Review the file in /Pending_Approval/email/")
    print("  2. To APPROVE: Move file to /Approved/")
    print("  3. To REJECT: Move file to /Rejected/")
    print()
    print("The orchestrator will automatically:")
    print("  - Detect when you move the file")
    print("  - Send the email (if approved)")
    print("  - Log the action")
    print("  - Archive the approval file to /Done/")
    print()

    # Step 3: Wait for action
    print("Step 3: Waiting for Human Action")
    print("-" * 60)
    print("Monitoring file location...")
    print("(Press Ctrl+C to stop monitoring)")
    print()

    base_dir = Path(__file__).parent.parent.parent
    pending_path = base_dir / "Pending_Approval" / "email" / filepath.name
    approved_path = base_dir / "Approved" / filepath.name
    rejected_path = base_dir / "Rejected" / filepath.name

    try:
        while True:
            if not pending_path.exists():
                if approved_path.exists():
                    print("✓ File moved to /Approved/")
                    print("  The orchestrator will send the email shortly...")
                    print()
                    print("Check:")
                    print("  - Orchestrator logs: /Logs/integration_orchestrator.log")
                    print("  - Email logs: /Logs/YYYY-MM-DD.json")
                    print("  - Done folder: /Done/")
                    break
                elif rejected_path.exists():
                    print("✗ File moved to /Rejected/")
                    print("  Email will NOT be sent")
                    print("  Rejection logged")
                    break
                else:
                    # Check Done folder (might have been processed already)
                    done_dir = base_dir / "Done"
                    if done_dir.exists():
                        done_files = list(done_dir.glob(f"*{filepath.name}"))
                        if done_files:
                            print("✓ Email already processed and sent!")
                            print(f"  Archived to: {done_files[0].name}")
                            break

            time.sleep(2)
            print(".", end="", flush=True)

    except KeyboardInterrupt:
        print()
        print()
        print("Monitoring stopped")
        print(f"Approval request still pending: {filepath.name}")

    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)


def show_status():
    """Show current status of approval workflow"""

    base_dir = Path(__file__).parent.parent.parent

    print("=" * 60)
    print("Email Approval Workflow Status")
    print("=" * 60)
    print()

    # Check directories
    dirs = {
        "Pending Approval": base_dir / "Pending_Approval" / "email",
        "Approved": base_dir / "Approved",
        "Rejected": base_dir / "Rejected",
        "Done": base_dir / "Done"
    }

    for name, path in dirs.items():
        if path.exists():
            files = list(path.glob("*.md"))
            print(f"{name:20} {len(files):3} files")
            if files:
                for f in files[:5]:  # Show first 5
                    print(f"  - {f.name}")
                if len(files) > 5:
                    print(f"  ... and {len(files) - 5} more")
        else:
            print(f"{name:20} (directory not found)")

    print()

    # Check state files
    state_files = {
        "Processed Events": Path(__file__).parent / "processed_events.json",
        "Processed Approvals": Path(__file__).parent / "processed_approvals.json"
    }

    print("State Files:")
    for name, path in state_files.items():
        if path.exists():
            import json
            with open(path) as f:
                data = json.load(f)
            print(f"  {name:25} {len(data)} entries")
        else:
            print(f"  {name:25} (not found)")

    print()
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        test_workflow()
