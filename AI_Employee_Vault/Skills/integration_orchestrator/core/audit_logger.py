#!/usr/bin/env python3
"""
AuditLogger - Structured Audit Logging
=======================================

Structured audit logging for compliance and traceability.
JSONL format for easy parsing and analysis with queryable audit trail.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class AuditLogger:
    """Structured audit logging for compliance"""

    def __init__(self, logs_dir: Path, logger: logging.Logger):
        self.logs_dir = logs_dir
        self.logger = logger
        self.audit_file = logs_dir / "audit.jsonl"

        # Ensure audit file exists
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.audit_file.exists():
            self.audit_file.touch()

        self.logger.info(f"AuditLogger initialized (file: {self.audit_file})")

    def log_event(self, event_type: str, actor: str, action: str,
                  resource: str, result: str, metadata: Dict[str, Any] = None):
        """Log an audit event"""
        try:
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'event_type': event_type,
                'actor': actor,
                'action': action,
                'resource': resource,
                'result': result,
                'metadata': metadata or {}
            }

            # Append to audit log
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_entry) + '\n')

        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")

    def log_skill_execution(self, skill_name: str, args: List[str],
                           result: Dict, duration: float):
        """Log skill execution"""
        self.log_event(
            event_type='skill_execution',
            actor='integration_orchestrator',
            action='execute_skill',
            resource=skill_name,
            result='success' if result.get('success') else 'failure',
            metadata={
                'args': args,
                'duration': duration,
                'returncode': result.get('returncode'),
                'error': result.get('stderr') if not result.get('success') else None
            }
        )

    def log_approval(self, email_id: str, action: str, result: str):
        """Log approval action"""
        self.log_event(
            event_type='approval',
            actor='user',
            action=action,
            resource=email_id,
            result=result,
            metadata={}
        )

    def log_email_sent(self, to: str, subject: str, result: str):
        """Log email sent"""
        self.log_event(
            event_type='email_sent',
            actor='integration_orchestrator',
            action='send_email',
            resource=to,
            result=result,
            metadata={'subject': subject}
        )

    def query_logs(self, event_type: str = None, start_time: datetime = None,
                   end_time: datetime = None, limit: int = 100) -> List[Dict]:
        """Query audit logs with filters"""
        try:
            results = []

            if not self.audit_file.exists():
                return results

            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        entry = json.loads(line.strip())

                        # Apply filters
                        if event_type and entry.get('event_type') != event_type:
                            continue

                        entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))

                        if start_time and entry_time < start_time:
                            continue

                        if end_time and entry_time > end_time:
                            continue

                        results.append(entry)

                        if len(results) >= limit:
                            break

                    except json.JSONDecodeError:
                        continue

            return results

        except Exception as e:
            self.logger.error(f"Error querying audit logs: {e}")
            return []
