#!/usr/bin/env python3
"""
SkillRegistry - Enhanced Skill Management
==========================================

Registry wrapper around SkillDispatcher with enhanced capabilities:
- Automatic retry on failure with exponential backoff
- Structured audit logging for all skill executions
- Skill metadata tracking (execution count, last run, etc.)
- Event emission for skill lifecycle
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock


class SkillRegistry:
    """Registry wrapper around SkillDispatcher with enhanced capabilities"""

    def __init__(self, dispatcher, event_bus, retry_queue, audit_logger, logger: logging.Logger):
        """
        Initialize SkillRegistry.

        Args:
            dispatcher: SkillDispatcher instance
            event_bus: EventBus instance
            retry_queue: RetryQueue instance
            audit_logger: AuditLogger instance
            logger: Logger instance
        """
        self.dispatcher = dispatcher
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.audit_logger = audit_logger
        self.logger = logger
        self.skill_metadata: Dict[str, Dict] = {}
        self.lock = Lock()

    def register_skill(self, skill_name: str, metadata: Dict = None):
        """Register a skill with metadata"""
        with self.lock:
            self.skill_metadata[skill_name] = {
                'name': skill_name,
                'registered_at': datetime.utcnow().isoformat() + 'Z',
                'execution_count': 0,
                'last_execution': None,
                'metadata': metadata or {}
            }
        self.logger.info(f"Registered skill: {skill_name}")

    def execute_skill(self, skill_name: str, args: List[str] = None,
                     retry_on_failure: bool = True) -> Dict:
        """Execute skill with enhanced error handling and retry"""
        start_time = time.time()

        # Publish pre-execution event
        self.event_bus.publish('skill_execution_started', {
            'skill_name': skill_name,
            'args': args,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

        # Execute skill
        result = self.dispatcher.execute_skill(skill_name, args)
        duration = time.time() - start_time

        # Update metadata
        with self.lock:
            if skill_name in self.skill_metadata:
                self.skill_metadata[skill_name]['execution_count'] += 1
                self.skill_metadata[skill_name]['last_execution'] = datetime.utcnow().isoformat() + 'Z'

        # Audit log
        self.audit_logger.log_skill_execution(skill_name, args or [], result, duration)

        # Handle failure
        if not result.get('success') and retry_on_failure:
            self.logger.warning(f"Skill {skill_name} failed, enqueueing for retry")
            # Use SkillRegistry.execute_skill (not dispatcher) to ensure audit logging and events
            self.retry_queue.enqueue(
                operation=self.execute_skill,
                args=(skill_name, args),
                kwargs={'retry_on_failure': False},  # Prevent infinite retry loop
                context={'name': f"skill_{skill_name}", 'skill': skill_name}
            )

        # Publish post-execution event
        self.event_bus.publish('skill_execution_completed', {
            'skill_name': skill_name,
            'success': result.get('success'),
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

        return result

    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """Get skill metadata"""
        with self.lock:
            return self.skill_metadata.get(skill_name)

    def list_skills(self) -> List[Dict]:
        """List all registered skills"""
        with self.lock:
            return list(self.skill_metadata.values())
