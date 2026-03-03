#!/usr/bin/env python3
"""
ApprovalManager - Approval Tracking
====================================

Tracks email approval processing to prevent duplicates.
Maintains state of processed approvals.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict


class ApprovalManager:
    """Tracks processed approvals to prevent duplicates"""

    def __init__(self, approval_file: Path):
        self.approval_file = approval_file
        self.processed_approvals: Dict[str, Dict] = {}
        self.load_approvals()

    def load_approvals(self):
        """Load processed approvals from file"""
        try:
            if self.approval_file.exists():
                with open(self.approval_file, 'r') as f:
                    self.processed_approvals = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load approval file: {e}")
            self.processed_approvals = {}

    def save_approvals(self):
        """Save processed approvals to file"""
        try:
            with open(self.approval_file, 'w') as f:
                json.dump(self.processed_approvals, f, indent=2)
        except Exception as e:
            print(f"Error saving approvals: {e}")

    def is_processed(self, approval_id: str) -> bool:
        """Check if approval has been processed"""
        return approval_id in self.processed_approvals

    def mark_processed(self, approval_id: str, metadata: Dict):
        """Mark approval as processed"""
        self.processed_approvals[approval_id] = {
            **metadata,
            'processed_at': datetime.utcnow().isoformat() + 'Z'
        }
        self.save_approvals()

    def get_approval_hash(self, email_id: str, action: str) -> str:
        """Generate unique hash for approval"""
        content = f"{email_id}_{action}"
        return hashlib.md5(content.encode()).hexdigest()
