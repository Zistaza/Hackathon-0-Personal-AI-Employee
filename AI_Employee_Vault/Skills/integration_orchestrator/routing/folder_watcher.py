#!/usr/bin/env python3
"""
FolderWatcherHandler - Filesystem Event Handler
================================================

Handles filesystem events using watchdog.
Routes file creation, modification, and move events to EventRouter.
"""

import logging
from pathlib import Path
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class FolderWatcherHandler(FileSystemEventHandler):
    """Handles filesystem events"""

    def __init__(self, folder_name: str, event_router, logger: logging.Logger):
        self.folder_name = folder_name
        self.event_router = event_router
        self.logger = logger

    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Only process markdown files
        if filepath.suffix != '.md':
            return

        # Route event
        event_type = f"{self.folder_name}_created"
        self.event_router.route_event(event_type, filepath)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Only process markdown files
        if filepath.suffix != '.md':
            return

        # Only route modifications for Pending_Approval
        if self.folder_name == "pending_approval":
            event_type = f"{self.folder_name}_modified"
            self.event_router.route_event(event_type, filepath)

    def on_moved(self, event: FileSystemEvent):
        """Handle file moves (for Approved/Rejected workflow)"""
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)

        # Only process markdown files
        if dest_path.suffix != '.md':
            return

        # Treat moves as creation in destination folder
        event_type = f"{self.folder_name}_created"
        self.event_router.route_event(event_type, dest_path)
