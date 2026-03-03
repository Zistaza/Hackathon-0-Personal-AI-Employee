#!/usr/bin/env python3
"""
StateManager - State Persistence
=================================

Manages processed events state and system-wide state tracking.
Enhanced for Gold Tier with metrics collection and persistence.
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock


class StateManager:
    """Manages processed events state - Enhanced for Gold Tier"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.processed_events: Dict[str, Dict] = {}
        # Gold Tier enhancements
        self.system_state: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        self.lock = Lock()
        self.load_state()

    def load_state(self):
        """Load processed events from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Support both old and new format
                    if isinstance(data, dict) and 'processed_events' in data:
                        # New format with enhanced state
                        self.processed_events = data.get('processed_events', {})
                        self.system_state = data.get('system_state', {})
                        self.metrics = data.get('metrics', {})
                    else:
                        # Old format - just processed events
                        self.processed_events = data
                        self.system_state = {}
                        self.metrics = {}
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
            self.processed_events = {}
            self.system_state = {}
            self.metrics = {}

    def save_state(self):
        """Save processed events to file - Enhanced format"""
        try:
            with self.lock:
                state_data = {
                    'processed_events': self.processed_events,
                    'system_state': self.system_state,
                    'metrics': self.metrics,
                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                }
                with open(self.state_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def is_processed(self, event_id: str) -> bool:
        """Check if event has been processed"""
        with self.lock:
            return event_id in self.processed_events

    def mark_processed(self, event_id: str, metadata: Dict):
        """Mark event as processed"""
        with self.lock:
            self.processed_events[event_id] = {
                **metadata,
                'processed_at': datetime.utcnow().isoformat() + 'Z'
            }
        self.save_state()

    def get_event_hash(self, filepath: Path) -> str:
        """Generate unique hash for file event"""
        try:
            stat = filepath.stat()
            content = f"{filepath.name}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return hashlib.md5(str(filepath).encode()).hexdigest()

    # Gold Tier enhancements
    def set_system_state(self, key: str, value: Any):
        """Set system state value"""
        with self.lock:
            self.system_state[key] = value
        self.save_state()

    def get_system_state(self, key: str, default: Any = None) -> Any:
        """Get system state value"""
        with self.lock:
            return self.system_state.get(key, default)

    def update_metric(self, metric_name: str, value: Any):
        """Update a metric"""
        with self.lock:
            self.metrics[metric_name] = {
                'value': value,
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        self.save_state()

    def get_metric(self, metric_name: str) -> Optional[Dict]:
        """Get a metric"""
        with self.lock:
            return self.metrics.get(metric_name)

    def increment_counter(self, counter_name: str, amount: int = 1):
        """Increment a counter metric"""
        with self.lock:
            if counter_name not in self.metrics:
                self.metrics[counter_name] = {'value': 0}
            self.metrics[counter_name]['value'] += amount
            self.metrics[counter_name]['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        self.save_state()
