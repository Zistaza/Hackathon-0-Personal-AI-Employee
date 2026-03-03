#!/usr/bin/env python3
"""
Watcher Manager
Runs multiple watchers concurrently in separate processes
"""

import sys
import signal
import time
from multiprocessing import Process
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from gmail_watcher import GmailWatcher
from whatsapp_watcher import WhatsAppWatcher
from linkedin_watcher import LinkedInWatcher
from facebook_watcher import FacebookWatcher
from instagram_watcher import InstagramWatcher
from twitter_watcher import TwitterWatcher


class WatcherManager:
    """Manages multiple watcher processes"""

    def __init__(self):
        self.processes = []
        self.running = False

    def start_watcher(self, watcher_class, name, **kwargs):
        """Start a watcher in a separate process"""
        def run_watcher():
            try:
                watcher = watcher_class(**kwargs)
                watcher.run()
            except Exception as e:
                print(f"Error in {name} watcher: {e}")

        process = Process(target=run_watcher, name=name)
        process.start()
        self.processes.append(process)
        print(f"Started {name} watcher (PID: {process.pid})")

    def start_all(self):
        """Start all configured watchers"""
        print("=" * 50)
        print("AI Employee Watcher Manager")
        print("=" * 50)
        print()

        self.running = True

        # Start Gmail Watcher
        try:
            self.start_watcher(
                GmailWatcher,
                "Gmail",
                check_interval=300,
                keywords=["invoice", "urgent", "payment", "proposal"],
                max_results=10
            )
        except Exception as e:
            print(f"Failed to start Gmail watcher: {e}")

        # Start WhatsApp Watcher
        try:
            self.start_watcher(
                WhatsAppWatcher,
                "WhatsApp",
                check_interval=300,
                keywords=["invoice", "urgent", "payment", "proposal"],
                headless=True,
                max_messages_per_chat=20
            )
        except Exception as e:
            print(f"Failed to start WhatsApp watcher: {e}")

        # Start LinkedIn Watcher
        try:
            self.start_watcher(
                LinkedInWatcher,
                "LinkedIn",
                check_interval=600,
                keywords=["job", "opportunity", "interview", "proposal", "project"],
                headless=True,
                monitor_messages=True,
                monitor_notifications=True
            )
        except Exception as e:
            print(f"Failed to start LinkedIn watcher: {e}")

        # Start Facebook Watcher
        try:
            self.start_watcher(
                FacebookWatcher,
                "Facebook",
                check_interval=600,
                keywords=["urgent", "important", "invoice", "payment", "proposal"],
                headless=True,
                monitor_notifications=True,
                monitor_messages=True
            )
        except Exception as e:
            print(f"Failed to start Facebook watcher: {e}")

        # Start Instagram Watcher
        try:
            self.start_watcher(
                InstagramWatcher,
                "Instagram",
                check_interval=600,
                keywords=["urgent", "important", "collab", "partnership", "business"],
                headless=True,
                monitor_notifications=True,
                monitor_messages=True
            )
        except Exception as e:
            print(f"Failed to start Instagram watcher: {e}")

        # Start Twitter/X Watcher
        try:
            self.start_watcher(
                TwitterWatcher,
                "Twitter",
                check_interval=600,
                keywords=["urgent", "important", "mention", "dm", "message"],
                headless=True,
                monitor_notifications=True,
                monitor_messages=True
            )
        except Exception as e:
            print(f"Failed to start Twitter watcher: {e}")

        print()
        print(f"Started {len(self.processes)} watcher(s)")
        print("Press Ctrl+C to stop all watchers")
        print()

    def stop_all(self):
        """Stop all running watchers"""
        print("\nStopping all watchers...")

        for process in self.processes:
            if process.is_alive():
                print(f"Stopping {process.name} (PID: {process.pid})...")
                process.terminate()
                process.join(timeout=5)

                if process.is_alive():
                    print(f"Force killing {process.name}...")
                    process.kill()
                    process.join()

        print("All watchers stopped")

    def monitor(self):
        """Monitor running watchers and restart if needed"""
        restart_config = {
            'Gmail': {
                'class': GmailWatcher,
                'kwargs': {
                    'check_interval': 300,
                    'keywords': ["invoice", "urgent", "payment", "proposal"],
                    'max_results': 10
                }
            },
            'WhatsApp': {
                'class': WhatsAppWatcher,
                'kwargs': {
                    'check_interval': 300,
                    'keywords': ["invoice", "urgent", "payment", "proposal"],
                    'headless': True,
                    'max_messages_per_chat': 20
                }
            },
            'LinkedIn': {
                'class': LinkedInWatcher,
                'kwargs': {
                    'check_interval': 600,
                    'keywords': ["job", "opportunity", "interview", "proposal", "project"],
                    'headless': True,
                    'monitor_messages': True,
                    'monitor_notifications': True
                }
            },
            'Facebook': {
                'class': FacebookWatcher,
                'kwargs': {
                    'check_interval': 600,
                    'keywords': ["urgent", "important", "invoice", "payment", "proposal"],
                    'headless': True,
                    'monitor_notifications': True,
                    'monitor_messages': True
                }
            },
            'Instagram': {
                'class': InstagramWatcher,
                'kwargs': {
                    'check_interval': 600,
                    'keywords': ["urgent", "important", "collab", "partnership", "business"],
                    'headless': True,
                    'monitor_notifications': True,
                    'monitor_messages': True
                }
            },
            'Twitter': {
                'class': TwitterWatcher,
                'kwargs': {
                    'check_interval': 600,
                    'keywords': ["urgent", "important", "mention", "dm", "message"],
                    'headless': True,
                    'monitor_notifications': True,
                    'monitor_messages': True
                }
            }
        }

        try:
            while self.running:
                # Check if any process died
                for i, process in enumerate(self.processes):
                    if not process.is_alive():
                        name = process.name
                        print(f"Warning: {name} watcher died (exit code: {process.exitcode})")

                        # Don't restart if it was terminated intentionally
                        if process.exitcode == -15 or process.exitcode == -9:
                            continue

                        # Get restart config
                        if name in restart_config:
                            config = restart_config[name]
                            print(f"Restarting {name} watcher...")

                            # Remove old process
                            self.processes.pop(i)

                            # Start new process
                            try:
                                self.start_watcher(
                                    config['class'],
                                    name,
                                    **config['kwargs']
                                )
                                print(f"Successfully restarted {name} watcher")
                            except Exception as e:
                                print(f"Failed to restart {name} watcher: {e}")

                        break  # Break to restart loop with updated process list

                time.sleep(10)

        except KeyboardInterrupt:
            print("\nReceived interrupt signal")

        finally:
            self.stop_all()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}")
        self.running = False


def main():
    """Main entry point"""
    manager = WatcherManager()

    # Setup signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)

    # Start all watchers
    manager.start_all()

    # Monitor watchers
    manager.monitor()


if __name__ == "__main__":
    main()
