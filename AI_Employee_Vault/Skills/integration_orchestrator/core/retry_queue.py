#!/usr/bin/env python3
"""
RetryQueue - Intelligent Retry Mechanism
=========================================

Queue for failed operations with configurable retry policies.
Handles transient failures gracefully with exponential backoff.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Callable
from threading import Lock, Thread, Event
from collections import deque
from enum import Enum


class RetryPolicy(Enum):
    """Retry policy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class RetryQueue:
    """Queue for failed operations with exponential backoff retry"""

    def __init__(self, logger: logging.Logger, max_retries: int = 5):
        self.logger = logger
        self.max_retries = max_retries
        self.queue: deque = deque()
        self.lock = Lock()
        self.running = False
        self.thread = None
        self.stop_event = Event()

    def enqueue(self, operation: Callable, args: tuple = (), kwargs: dict = None,
                policy: RetryPolicy = RetryPolicy.EXPONENTIAL, context: Dict = None):
        """Add operation to retry queue"""
        with self.lock:
            retry_item = {
                'operation': operation,
                'args': args,
                'kwargs': kwargs or {},
                'policy': policy,
                'context': context or {},
                'attempts': 0,
                'next_retry': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            self.queue.append(retry_item)
            self.logger.info(f"Enqueued operation for retry: {context.get('name', 'unknown')}")

    def start(self):
        """Start retry queue processor"""
        self.running = True
        self.thread = Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        self.logger.info("RetryQueue started")

    def stop(self):
        """Stop retry queue processor"""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("RetryQueue stopped")

    def _calculate_backoff(self, attempts: int, policy: RetryPolicy) -> int:
        """Calculate backoff delay in seconds"""
        if policy == RetryPolicy.EXPONENTIAL:
            return min(300, 2 ** attempts)  # Max 5 minutes
        elif policy == RetryPolicy.LINEAR:
            return min(300, 30 * attempts)  # 30s, 60s, 90s...
        else:  # FIXED
            return 60

    def _process_queue(self):
        """Process retry queue"""
        while self.running:
            try:
                now = datetime.utcnow()
                items_to_retry = []

                with self.lock:
                    # Find items ready for retry
                    for item in list(self.queue):
                        if item['next_retry'] <= now:
                            items_to_retry.append(item)
                            self.queue.remove(item)

                # Process items outside lock
                for item in items_to_retry:
                    self._retry_operation(item)

                # Sleep for 5 seconds
                if self.stop_event.wait(timeout=5):
                    break

            except Exception as e:
                self.logger.error(f"Error processing retry queue: {e}")
                time.sleep(5)

    def _retry_operation(self, item: Dict):
        """Retry a single operation"""
        item['attempts'] += 1
        context = item['context']
        operation_name = context.get('name', 'unknown')

        self.logger.info(f"Retrying operation: {operation_name} (attempt {item['attempts']}/{self.max_retries})")

        try:
            # Execute operation
            result = item['operation'](*item['args'], **item['kwargs'])

            # Check if successful
            if isinstance(result, dict) and result.get('success'):
                self.logger.info(f"Retry successful for: {operation_name}")
                return True
            else:
                raise Exception(f"Operation returned failure: {result}")

        except Exception as e:
            self.logger.warning(f"Retry failed for {operation_name}: {e}")

            # Re-enqueue if under max retries
            if item['attempts'] < self.max_retries:
                backoff = self._calculate_backoff(item['attempts'], item['policy'])
                item['next_retry'] = datetime.utcnow() + timedelta(seconds=backoff)

                with self.lock:
                    self.queue.append(item)

                self.logger.info(f"Re-enqueued {operation_name}, next retry in {backoff}s")
            else:
                self.logger.error(f"Max retries exceeded for {operation_name}, giving up")
                return False

    def get_queue_size(self) -> int:
        """Get current queue size"""
        with self.lock:
            return len(self.queue)
