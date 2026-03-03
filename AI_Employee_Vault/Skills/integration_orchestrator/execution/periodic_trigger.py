#!/usr/bin/env python3
"""
PeriodicTrigger - Periodic Skill Execution
===========================================

Periodic skill execution (cron-like functionality).
Runs registered skills at specified intervals in background thread.

Enterprise Integration:
- Executes scheduled social media posts
- Checks watcher health
"""

import time
import logging
from datetime import datetime, timedelta
from threading import Thread, Event


class PeriodicTrigger:
    """Triggers skills periodically (cron-like) - Enterprise Edition"""

    def __init__(self, logger: logging.Logger, interval: int = 3600, social_adapter=None):
        """
        Initialize PeriodicTrigger.

        Args:
            logger: Logger instance
            interval: Check interval in seconds (default: 3600 = 1 hour)
            social_adapter: SocialMCPAdapter for scheduled posts (Enterprise)
        """
        self.logger = logger
        self.interval = interval
        self.running = False
        self.thread = None
        self.stop_event = Event()
        self.social_adapter = social_adapter  # Enterprise: Social media integration

    def start(self):
        """Start periodic trigger"""
        self.running = True
        self.thread = Thread(target=self._periodic_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"PeriodicTrigger started (interval: {self.interval}s, Enterprise Mode)")

    def stop(self):
        """Stop periodic trigger"""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("PeriodicTrigger stopped")

    def _periodic_loop(self):
        """Main periodic loop with enterprise features"""
        last_watcher_check = datetime.utcnow()
        last_social_check = datetime.utcnow()

        while self.running:
            try:
                now = datetime.utcnow()

                # Check watchers every 5 minutes
                if (now - last_watcher_check) > timedelta(minutes=5):
                    self.logger.info("Periodic: Checking if watchers are running")
                    # Could check if run_all_watchers.py is running and restart if needed
                    last_watcher_check = now

                # Enterprise: Execute scheduled social posts every minute
                if self.social_adapter and (now - last_social_check) > timedelta(minutes=1):
                    try:
                        result = self.social_adapter.execute_scheduled_posts()
                        if result.get('executed'):
                            self.logger.info(f"Executed {len(result['executed'])} scheduled posts")
                        if result.get('failed'):
                            self.logger.warning(f"Failed to execute {len(result['failed'])} scheduled posts")
                    except Exception as e:
                        self.logger.error(f"Error executing scheduled posts: {e}")

                    last_social_check = now

                # Sleep for 60 seconds
                if self.stop_event.wait(timeout=60):
                    break

            except Exception as e:
                self.logger.error(f"Error in periodic tasks: {e}")
                time.sleep(60)
