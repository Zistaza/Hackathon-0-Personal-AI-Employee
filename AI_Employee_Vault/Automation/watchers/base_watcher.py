#!/usr/bin/env python3
"""
Base Watcher Class
Abstract base class for all watcher implementations
Provides common functionality: logging, file creation, duplicate tracking, continuous running
"""

import os
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import signal
import sys


class BaseWatcher(ABC):
    """Abstract base class for all watchers"""

    def __init__(
        self,
        name: str,
        needs_action_dir: str = "../../Needs_Action",
        logs_dir: str = "../../Logs",
        check_interval: int = 300,  # 5 minutes default
        keywords: Optional[List[str]] = None
    ):
        """
        Initialize base watcher

        Args:
            name: Watcher name (e.g., "gmail", "whatsapp")
            needs_action_dir: Path to Needs_Action directory
            logs_dir: Path to Logs directory
            check_interval: Seconds between checks
            keywords: List of keywords to filter for
        """
        self.name = name
        self.base_dir = Path(__file__).parent.parent.parent
        self.needs_action_dir = self.base_dir / needs_action_dir.lstrip("../../")
        self.logs_dir = self.base_dir / logs_dir.lstrip("../../")
        self.check_interval = check_interval
        self.keywords = [k.lower() for k in (keywords or [])]

        # Tracking file for processed items
        self.tracking_file = Path(__file__).parent / f"{name}_processed.json"
        self.processed_ids: Set[str] = set()

        # Running state
        self.running = False

        # Setup
        self._setup_directories()
        self._setup_logging()
        self._load_processed_ids()
        self._setup_signal_handlers()

    def _setup_directories(self):
        """Create required directories if they don't exist"""
        self.needs_action_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging configuration"""
        log_file = self.logs_dir / f"{self.name}_watcher.log"

        # Create logger
        self.logger = logging.getLogger(f"{self.name}_watcher")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        self.logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _load_processed_ids(self):
        """Load processed IDs from tracking file"""
        try:
            if self.tracking_file.exists():
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    self.processed_ids = set(data)
                self.logger.info(f"Loaded {len(self.processed_ids)} processed IDs")
            else:
                self.processed_ids = set()
                self.logger.info("No existing tracking file, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading processed IDs: {e}")
            self.processed_ids = set()

    def _save_processed_ids(self):
        """Save processed IDs to tracking file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(list(self.processed_ids), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving processed IDs: {e}")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def is_processed(self, item_id: str) -> bool:
        """Check if item has already been processed"""
        return item_id in self.processed_ids

    def mark_processed(self, item_id: str):
        """Mark item as processed"""
        self.processed_ids.add(item_id)
        self._save_processed_ids()

    def contains_keyword(self, text: str) -> bool:
        """Check if text contains any of the configured keywords"""
        if not self.keywords:
            return True  # No keywords = process everything

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    def create_action_file(
        self,
        content: str,
        metadata: Dict[str, str],
        filename_prefix: Optional[str] = None
    ) -> Optional[str]:
        """
        Create markdown file in Needs_Action directory

        Args:
            content: Main content of the file
            metadata: Dictionary of metadata fields
            filename_prefix: Optional prefix for filename

        Returns:
            Filename if successful, None otherwise
        """
        try:
            # Generate filename
            timestamp = int(time.time() * 1000)
            prefix = filename_prefix or self.name
            filename = f"{prefix}_{timestamp}.md"
            filepath = self.needs_action_dir / filename

            # Build frontmatter
            frontmatter_lines = ["---"]
            for key, value in metadata.items():
                frontmatter_lines.append(f"{key}: {value}")
            frontmatter_lines.append("---")
            frontmatter = "\n".join(frontmatter_lines)

            # Write file
            full_content = f"{frontmatter}\n\n{content}\n"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)

            self.logger.info(f"Created action file: {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the watcher (connect to services, authenticate, etc.)

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def check_for_events(self) -> List[Dict]:
        """
        Check for new events/messages

        Returns:
            List of event dictionaries with keys:
            - id: Unique identifier
            - content: Main content
            - metadata: Dictionary of metadata fields
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Cleanup resources before shutdown"""
        pass

    def process_events(self, events: List[Dict]) -> int:
        """
        Process list of events

        Args:
            events: List of event dictionaries

        Returns:
            Number of events processed
        """
        processed_count = 0

        for event in events:
            try:
                event_id = event.get('id')
                content = event.get('content', '')
                metadata = event.get('metadata', {})

                # Skip if already processed
                if self.is_processed(event_id):
                    continue

                # Skip if doesn't contain keywords
                if not self.contains_keyword(content):
                    continue

                # Create action file
                filename = self.create_action_file(content, metadata)

                if filename:
                    # Mark as processed
                    self.mark_processed(event_id)
                    processed_count += 1
                    self.logger.info(f"Processed event: {event_id}")

            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
                continue

        return processed_count

    def run_once(self) -> bool:
        """
        Run one check cycle

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting check cycle...")

            # Check for events
            events = self.check_for_events()
            self.logger.info(f"Found {len(events)} event(s)")

            # Process events
            if events:
                processed = self.process_events(events)
                self.logger.info(f"Processed {processed} new event(s)")

            return True

        except Exception as e:
            self.logger.error(f"Error in check cycle: {e}")
            return False

    def run(self):
        """Run the watcher continuously"""
        self.logger.info(f"Starting {self.name} watcher...")
        self.logger.info(f"Check interval: {self.check_interval} seconds")
        self.logger.info(f"Keywords: {self.keywords if self.keywords else 'None (all events)'}")

        # Initialize
        if not self.initialize():
            self.logger.error("Initialization failed, exiting")
            return

        self.running = True

        try:
            while self.running:
                # Run check cycle
                self.run_once()

                # Sleep until next check
                if self.running:
                    self.logger.info(f"Sleeping for {self.check_interval} seconds...")
                    time.sleep(self.check_interval)

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")

        finally:
            self.logger.info("Shutting down...")
            self.cleanup()
            self.logger.info("Shutdown complete")


if __name__ == "__main__":
    print("BaseWatcher is an abstract class and cannot be run directly")
    print("Use a specific watcher implementation (gmail_watcher.py, etc.)")
