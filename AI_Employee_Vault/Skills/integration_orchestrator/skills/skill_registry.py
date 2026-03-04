#!/usr/bin/env python3
"""
SkillRegistry - Enhanced Skill Management with MCP Integration
===============================================================

Registry wrapper around SkillDispatcher with enhanced capabilities:
- Automatic retry on failure with exponential backoff
- Structured audit logging for all skill executions
- Skill metadata tracking (execution count, last run, etc.)
- Event emission for skill lifecycle
- MCP (Modular Component Protocol) execution support
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock


class SkillRegistry:
    """Registry wrapper around SkillDispatcher with MCP integration"""

    def __init__(self, dispatcher, event_bus, retry_queue, audit_logger, logger: logging.Logger, mcp_manager=None):
        """
        Initialize SkillRegistry.

        Args:
            dispatcher: SkillDispatcher instance
            event_bus: EventBus instance
            retry_queue: RetryQueue instance
            audit_logger: AuditLogger instance
            logger: Logger instance
            mcp_manager: MCPServerManager instance (optional)
        """
        self.dispatcher = dispatcher
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.audit_logger = audit_logger
        self.logger = logger
        self.mcp_manager = mcp_manager
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

    def set_mcp_manager(self, mcp_manager):
        """Set MCP manager after initialization."""
        self.mcp_manager = mcp_manager
        self.logger.info("MCP manager attached to SkillRegistry")

    def execute_skill(self, skill_name: str, args: List[str] = None,
                     retry_on_failure: bool = True) -> Dict:
        """Execute skill with enhanced error handling, retry, and MCP support"""
        start_time = time.time()

        # Publish pre-execution event
        self.event_bus.publish('skill_execution_started', {
            'skill_name': skill_name,
            'args': args,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

        # Try MCP execution first if MCP manager is available
        if self.mcp_manager:
            mcp_result = self.mcp_manager.execute_via_mcp(skill_name, args)

            if mcp_result.get('via_mcp'):
                # Execution went through MCP
                duration = time.time() - start_time

                # Convert MCP result to standard format
                result = {
                    'success': mcp_result['success'],
                    'stdout': str(mcp_result.get('data', '')),
                    'stderr': mcp_result.get('error', ''),
                    'returncode': 0 if mcp_result['success'] else 1,
                    'via_mcp': True,
                    'mcp_server': mcp_result.get('mcp_server'),
                    'mcp_action': mcp_result.get('mcp_action')
                }

                self.logger.info(f"✓ Skill '{skill_name}' executed via MCP: {result.get('mcp_server')}.{result.get('mcp_action')}")
            else:
                # MCP not available for this skill, fall back to direct execution
                self.logger.debug(f"MCP not available for '{skill_name}', using direct execution")
                result = self.dispatcher.execute_skill(skill_name, args)
                result['via_mcp'] = False
                duration = time.time() - start_time
        else:
            # No MCP manager, use direct execution
            result = self.dispatcher.execute_skill(skill_name, args)
            result['via_mcp'] = False
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
            'via_mcp': result.get('via_mcp', False),
            'mcp_server': result.get('mcp_server'),
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
