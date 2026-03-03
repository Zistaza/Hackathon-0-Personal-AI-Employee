#!/usr/bin/env python3
"""
HealthMonitor - Component Health Monitoring
============================================

Continuous component health monitoring with periodic health checks.
Tracks health status of all system components and provides overall system health assessment.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Callable, Optional
from threading import Lock, Thread, Event
from enum import Enum


class ComponentStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthMonitor:
    """Continuous component health monitoring"""

    def __init__(self, logger: logging.Logger, check_interval: int = 60):
        self.logger = logger
        self.check_interval = check_interval
        self.health_checks: Dict[str, Callable] = {}
        self.component_status: Dict[str, Dict] = {}
        self.lock = Lock()
        self.running = False
        self.thread = None
        self.stop_event = Event()

    def register_health_check(self, component_name: str, check_function: Callable):
        """Register a health check for a component"""
        with self.lock:
            self.health_checks[component_name] = check_function
            self.component_status[component_name] = {
                'status': ComponentStatus.UNKNOWN,
                'last_check': None,
                'message': 'Not yet checked'
            }
        self.logger.info(f"Registered health check for: {component_name}")

    def register_component(self, name: str, check_function: Callable):
        """Register a component with health check (alias for register_health_check)"""
        self.register_health_check(name, check_function)

    def start(self):
        """Start health monitoring"""
        self.running = True
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"HealthMonitor started (check interval: {self.check_interval}s)")

    def stop(self):
        """Stop health monitoring"""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("HealthMonitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_all_components()

                # Sleep until next check
                if self.stop_event.wait(timeout=self.check_interval):
                    break

            except Exception as e:
                self.logger.error(f"Error in health monitor loop: {e}")
                time.sleep(self.check_interval)

    def _check_all_components(self):
        """Check health of all registered components"""
        with self.lock:
            checks = list(self.health_checks.items())

        for component_name, check_function in checks:
            try:
                result = check_function()

                with self.lock:
                    self.component_status[component_name] = {
                        'status': result.get('status', ComponentStatus.UNKNOWN),
                        'last_check': datetime.utcnow().isoformat() + 'Z',
                        'message': result.get('message', 'No message')
                    }

            except Exception as e:
                self.logger.error(f"Health check failed for {component_name}: {e}")
                with self.lock:
                    self.component_status[component_name] = {
                        'status': ComponentStatus.UNHEALTHY,
                        'last_check': datetime.utcnow().isoformat() + 'Z',
                        'message': f'Health check error: {str(e)}'
                    }

    def get_component_health(self, component_name: str) -> Optional[Dict]:
        """Get health status of a specific component"""
        with self.lock:
            return self.component_status.get(component_name)

    def get_component_status(self, component_name: str) -> Optional[Dict]:
        """Get health status of a specific component (alias for get_component_health)"""
        return self.get_component_health(component_name)

    def get_system_health(self) -> Dict:
        """Get overall system health"""
        with self.lock:
            components = self.component_status.copy()

        # Determine overall status
        statuses = [comp['status'] for comp in components.values()]

        if not statuses:
            overall_status = ComponentStatus.UNKNOWN
        elif any(s == ComponentStatus.UNHEALTHY for s in statuses):
            overall_status = ComponentStatus.UNHEALTHY
        elif any(s == ComponentStatus.DEGRADED for s in statuses):
            overall_status = ComponentStatus.DEGRADED
        elif all(s == ComponentStatus.HEALTHY for s in statuses):
            overall_status = ComponentStatus.HEALTHY
        else:
            overall_status = ComponentStatus.UNKNOWN

        return {
            'overall_status': overall_status,
            'components': components,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
