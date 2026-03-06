"""
Execution Components
====================

Components for autonomous execution and task management:
- EmailExecutor: Email sending via MCP server
- PeriodicTrigger: Periodic skill execution
- GracefulDegradation: Automatic feature degradation
- AutonomousExecutor: Autonomous execution layer (Ralph Wiggum Loop)
- ApprovedFolderMonitor: Automatic execution of approved posts/messages
"""

from .email_executor import EmailExecutor
from .periodic_trigger import PeriodicTrigger
from .graceful_degradation import GracefulDegradation
from .autonomous_executor import AutonomousExecutor
from .approved_folder_monitor import ApprovedFolderMonitor

__all__ = [
    'EmailExecutor',
    'PeriodicTrigger',
    'GracefulDegradation',
    'AutonomousExecutor',
    'ApprovedFolderMonitor',
]
