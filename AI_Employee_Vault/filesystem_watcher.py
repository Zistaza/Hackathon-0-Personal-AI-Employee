#!/usr/bin/env python3
"""
Bronze Tier AI Employee - Filesystem Watcher
Monitors /Inbox folder and automatically moves new files to /Needs_Action
"""

import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('filesystem_watcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class InboxHandler(FileSystemEventHandler):
    """Handles file system events in the Inbox folder"""

    def __init__(self, inbox_path, needs_action_path):
        super().__init__()
        self.inbox_path = Path(inbox_path).resolve()
        self.needs_action_path = Path(needs_action_path).resolve()
        self.processing = set()  # Track files currently being processed

        # Validate paths
        if not self.inbox_path.exists():
            raise ValueError(f"Inbox path does not exist: {self.inbox_path}")
        if not self.needs_action_path.exists():
            raise ValueError(f"Needs_Action path does not exist: {self.needs_action_path}")

        logger.info(f"Monitoring: {self.inbox_path}")
        logger.info(f"Target: {self.needs_action_path}")

    def on_created(self, event):
        """Handle file creation events"""
        # Ignore directory creation
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore hidden files and temp files
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return

        # Ignore if already processing this file
        if str(file_path) in self.processing:
            return

        # Process the file
        self.process_file(file_path)

    def process_file(self, file_path):
        """Process a newly created file"""
        try:
            # Mark as processing
            self.processing.add(str(file_path))

            logger.info(f"Detected new file: {file_path.name}")

            # Wait briefly to ensure file is fully written
            # This handles cases where large files are still being copied
            time.sleep(0.5)

            # Verify file still exists and is readable
            if not file_path.exists():
                logger.warning(f"File disappeared before processing: {file_path.name}")
                return

            # Check if file is still being written (size changing)
            initial_size = file_path.stat().st_size
            time.sleep(0.2)
            if file_path.exists() and file_path.stat().st_size != initial_size:
                logger.info(f"File still being written, waiting: {file_path.name}")
                time.sleep(1.0)

            # Determine destination path
            destination = self.needs_action_path / file_path.name

            # Handle filename conflicts
            if destination.exists():
                destination = self.get_unique_filename(destination)
                logger.warning(f"File exists, using unique name: {destination.name}")

            # Move the file
            try:
                file_path.rename(destination)
                logger.info(f"✓ Moved to Needs_Action: {file_path.name} → {destination.name}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Moved: {file_path.name} → /Needs_Action/")
            except PermissionError as e:
                logger.error(f"Permission denied moving file: {file_path.name} - {e}")
            except OSError as e:
                logger.error(f"OS error moving file: {file_path.name} - {e}")

        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}", exc_info=True)
        finally:
            # Remove from processing set
            self.processing.discard(str(file_path))

    def get_unique_filename(self, path):
        """Generate a unique filename if destination already exists"""
        base_path = path.parent
        stem = path.stem
        suffix = path.suffix
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = base_path / new_name
            if not new_path.exists():
                return new_path
            counter += 1

            # Safety limit
            if counter > 1000:
                raise ValueError(f"Could not generate unique filename for: {path.name}")


class FilesystemWatcher:
    """Main watcher class"""

    def __init__(self, vault_path=None):
        # Determine vault path
        if vault_path is None:
            vault_path = Path(__file__).parent.resolve()
        else:
            vault_path = Path(vault_path).resolve()

        self.vault_path = vault_path
        self.inbox_path = vault_path / "Inbox"
        self.needs_action_path = vault_path / "Needs_Action"

        # Validate paths
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        if not self.inbox_path.exists():
            raise ValueError(f"Inbox folder not found: {self.inbox_path}")
        if not self.needs_action_path.exists():
            raise ValueError(f"Needs_Action folder not found: {self.needs_action_path}")

        self.observer = None
        self.running = False

    def start(self):
        """Start watching the Inbox folder"""
        try:
            logger.info("=" * 60)
            logger.info("Bronze Tier AI Employee - Filesystem Watcher")
            logger.info("=" * 60)
            logger.info(f"Vault: {self.vault_path}")
            logger.info(f"Watching: {self.inbox_path}")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)

            # Create event handler
            event_handler = InboxHandler(self.inbox_path, self.needs_action_path)

            # Create and start observer
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.inbox_path), recursive=False)
            self.observer.start()
            self.running = True

            logger.info("✓ Watcher started successfully")
            print("\n✓ Filesystem watcher is running...")
            print(f"✓ Monitoring: {self.inbox_path}")
            print("✓ Press Ctrl+C to stop\n")

            # Keep running
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()

        except Exception as e:
            logger.error(f"Failed to start watcher: {e}", exc_info=True)
            sys.exit(1)

    def stop(self):
        """Stop the watcher gracefully"""
        if self.observer and self.running:
            logger.info("Stopping watcher...")
            print("\n\nStopping filesystem watcher...")
            self.running = False
            self.observer.stop()
            self.observer.join(timeout=5)
            logger.info("✓ Watcher stopped")
            print("✓ Watcher stopped gracefully\n")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Parse command line arguments
    vault_path = None
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
        print(f"Using vault path: {vault_path}")

    # Create and start watcher
    try:
        watcher = FilesystemWatcher(vault_path)
        watcher.start()
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
