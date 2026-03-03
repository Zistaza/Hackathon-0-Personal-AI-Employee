#!/usr/bin/env python3
"""
GracefulDegradation - Automatic Feature Degradation
====================================================

Handles graceful degradation when components fail.
Monitors system health and disables non-critical features to prevent cascading failures.
"""

import logging
from typing import Dict, Set


class GracefulDegradation:
    """Handles graceful degradation when components fail"""

    def __init__(self, health_monitor, logger: logging.Logger):
        """
        Initialize GracefulDegradation.

        Args:
            health_monitor: HealthMonitor instance
            logger: Logger instance
        """
        self.health_monitor = health_monitor
        self.logger = logger
        self.degraded_mode = False
        self.disabled_features: Set[str] = set()

    def check_and_degrade(self) -> bool:
        """Check system health and enable degradation if needed"""
        from core.health_monitor import ComponentStatus

        health = self.health_monitor.get_system_health()
        overall_status = health['overall_status']

        if overall_status == ComponentStatus.UNHEALTHY:
            if not self.degraded_mode:
                self.logger.warning("System unhealthy, entering degraded mode")
                self._enter_degraded_mode(health['components'])
            return True
        elif overall_status == ComponentStatus.DEGRADED:
            self.logger.info("System degraded, some features may be limited")
            return True
        else:
            if self.degraded_mode:
                self.logger.info("System recovered, exiting degraded mode")
                self._exit_degraded_mode()
            return False

    def _enter_degraded_mode(self, components: Dict):
        """Enter degraded mode and disable non-critical features"""
        from core.health_monitor import ComponentStatus

        self.degraded_mode = True

        # Disable non-critical features based on component health
        for name, status in components.items():
            if status['status'] == ComponentStatus.UNHEALTHY:
                if 'email' in name.lower():
                    self.disabled_features.add('email_sending')
                    self.logger.warning("Disabled email sending due to unhealthy component")
                elif 'periodic' in name.lower():
                    self.disabled_features.add('periodic_triggers')
                    self.logger.warning("Disabled periodic triggers due to unhealthy component")

    def _exit_degraded_mode(self):
        """Exit degraded mode and re-enable features"""
        self.degraded_mode = False
        self.disabled_features.clear()
        self.logger.info("All features re-enabled")

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return feature not in self.disabled_features
