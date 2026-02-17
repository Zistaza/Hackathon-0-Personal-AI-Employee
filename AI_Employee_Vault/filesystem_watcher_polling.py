#!/usr/bin/env python3
"""
Bronze Tier AI Employee - Filesystem Watcher (Polling Mode)
Monitors /Inbox folder and automatically moves new files to /Needs_Action
WSL-compatible version using polling instead of inotify events
"""

import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime

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


class InboxPoller:
    """Polls the Inbox folder for new files"""

    def __init__(self, inbox_path, needs_action_path, poll_interval=2):
        self.inbox_path = Path(inbox_path).resolve()
        self.needs_action_path = Path(needs_action_path).resolve()
        self.poll_interval = poll_interval
        self.known_files = set()
        self.processing = set()

        # Validate paths
        if not self.inbox_path.exists():
            raise ValueError(f"Inbox path does not exist: {self.inbox_path}")
        if not self.needs_action_path.exists():
            raise ValueError(f"Needs_Action path does not exist: {self.needs_action_path}")

        # Initialize known files (don't process existing files on startup)
        self._scan_existing_files()

        logger.info(f"Monitoring: {self.inbox_path}")
        logger.info(f"Target: {self.needs_action_path}")
        logger.info(f"Poll interval: {self.poll_interval} seconds")

    def _scan_existing_files(self):
        """Scan and record existing files (don't process them)"""
        try:
            for file_path in self.inbox_path.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    self.known_files.add(file_path.name)
            if self.known_files:
                logger.info(f"Found {len(self.known_files)} existing files in Inbox (will not process)")
        except Exception as e:
            logger.error(f"Error scanning existing files: {e}")

    def poll(self):
        """Poll the Inbox folder for new files"""
        try:
            current_files = set()

            # Get current files in Inbox
            for file_path in self.inbox_path.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.') and not file_path.name.startswith('~'):
                    current_files.add(file_path.name)

            # Find new files
            new_files = current_files - self.known_files

            # Process new files
            for filename in new_files:
                file_path = self.inbox_path / filename
                if filename not in self.processing:
                    self.process_file(file_path)
                    self.known_files.add(filename)

            # Remove files that no longer exist from known_files
            self.known_files = self.known_files.intersection(current_files)

        except Exception as e:
            logger.error(f"Error during polling: {e}", exc_info=True)

    def process_file(self, file_path):
        """Process a newly detected file"""
        try:
            # Mark as processing
            self.processing.add(file_path.name)

            logger.info(f"Detected new file: {file_path.name}")

            # Wait briefly to ensure file is fully written
            time.sleep(0.5)

            # Verify file still exists and is readable
            if not file_path.exists():
                logger.warning(f"File disappeared before processing: {file_path.name}")
                return

            # Check if file is still being written (size changing)
            initial_size = file_path.stat().st_size
            time.sleep(0.3)
            if file_path.exists() and file_path.stat().st_size != initial_size:
                logger.info(f"File still being written, will retry: {file_path.name}")
                self.processing.discard(file_path.name)
                self.known_files.discard(file_path.name)
                return

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
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Moved: {file_path.name} → /Needs_Action/")
            except PermissionError as e:
                logger.error(f"Permission denied moving file: {file_path.name} - {e}")
            except OSError as e:
                logger.error(f"OS error moving file: {file_path.name} - {e}")

        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}", exc_info=True)
        finally:
            # Remove from processing set
            self.processing.discard(file_path.name)

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
    """Main watcher class using polling"""

    def __init__(self, vault_path=None, poll_interval=2):
        # Determine vault path
        if vault_path is None:
            vault_path = Path(__file__).parent.resolve()
        else:
            vault_path = Path(vault_path).resolve()

        self.vault_path = vault_path
        self.inbox_path = vault_path / "Inbox"
        self.needs_action_path = vault_path / "Needs_Action"
        self.poll_interval = poll_interval

        # Validate paths
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        if not self.inbox_path.exists():
            raise ValueError(f"Inbox folder not found: {self.inbox_path}")
        if not self.needs_action_path.exists():
            raise ValueError(f"Needs_Action folder not found: {self.needs_action_path}")

        self.poller = None
        self.running = False

    def start(self):
        """Start polling the Inbox folder"""
        try:
            logger.info("=" * 60)
            logger.info("Bronze Tier AI Employee - Filesystem Watcher")
            logger.info("(Polling Mode - WSL Compatible)")
            logger.info("=" * 60)
            logger.info(f"Vault: {self.vault_path}")
            logger.info(f"Watching: {self.inbox_path}")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)

            # Create poller
            self.poller = InboxPoller(self.inbox_path, self.needs_action_path, self.poll_interval)
            self.running = True

            logger.info("✓ Watcher started successfully")
            print("\n✓ Filesystem watcher is running (polling mode)...")
            print(f"✓ Monitoring: {self.inbox_path}")
            print(f"✓ Checking every {self.poll_interval} seconds")
            print("✓ Press Ctrl+C to stop\n")

            # Keep polling
            try:
                while self.running:
                    self.poller.poll()
                    time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                self.stop()

        except Exception as e:
            logger.error(f"Failed to start watcher: {e}", exc_info=True)
            sys.exit(1)

    def stop(self):
        """Stop the watcher gracefully"""
        if self.running:
            logger.info("Stopping watcher...")
            print("\n\nStopping filesystem watcher...")
            self.running = False
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
    poll_interval = 2  # Default: check every 2 seconds

    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
        print(f"Using vault path: {vault_path}")

    if len(sys.argv) > 2:
        try:
            poll_interval = int(sys.argv[2])
            print(f"Using poll interval: {poll_interval} seconds")
        except ValueError:
            print("Invalid poll interval, using default: 2 seconds")

    # Create and start watcher
    try:
        watcher = FilesystemWatcher(vault_path, poll_interval)
        watcher.start()
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
