"""
Event Routing Components
=========================

Components for filesystem event routing and handling:
- EventRouter: Routes filesystem events to appropriate handlers
- FolderWatcherHandler: Filesystem event handler using watchdog
"""

from .event_router import EventRouter
from .folder_watcher import FolderWatcherHandler

__all__ = [
    'EventRouter',
    'FolderWatcherHandler',
]
