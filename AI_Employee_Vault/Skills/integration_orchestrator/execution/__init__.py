"""
Execution Components
====================

Components for autonomous execution and task management:
- EmailExecutor: Email sending via MCP server
- PeriodicTrigger: Periodic skill execution
- GracefulDegradation: Automatic feature degradation
- AutonomousExecutor: Autonomous execution layer (Ralph Wiggum Loop)
"""

from .email_executor import EmailExecutor
from .periodic_trigger import PeriodicTrigger
from .graceful_degradation import GracefulDegradation
from .autonomous_executor import AutonomousExecutor

__all__ = [
    'EmailExecutor',
    'PeriodicTrigger',
    'GracefulDegradation',
    'AutonomousExecutor',
]
