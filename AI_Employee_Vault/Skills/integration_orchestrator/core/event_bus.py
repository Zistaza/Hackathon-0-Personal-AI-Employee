#!/usr/bin/env python3
"""
EventBus - Central Pub/Sub Event System
========================================

Central pub/sub event bus for inter-component communication.
Enables reactive programming patterns and decouples components.
"""

import logging
from typing import Dict, List, Callable, Any
from threading import Lock


class EventBus:
    """Central pub/sub event bus for inter-component communication"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.subscribers: Dict[str, List[Callable]] = {}
        self.lock = Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
            self.logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        with self.lock:
            if event_type in self.subscribers:
                try:
                    self.subscribers[event_type].remove(callback)
                    self.logger.debug(f"Unsubscribed from event: {event_type}")
                except ValueError:
                    pass

    def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to all subscribers"""
        with self.lock:
            subscribers = self.subscribers.get(event_type, []).copy()

        if subscribers:
            self.logger.debug(f"Publishing event: {event_type} to {len(subscribers)} subscribers")
            for callback in subscribers:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event subscriber for {event_type}: {e}")

    def clear(self):
        """Clear all subscriptions"""
        with self.lock:
            self.subscribers.clear()
