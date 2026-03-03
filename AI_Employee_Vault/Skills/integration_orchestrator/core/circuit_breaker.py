#!/usr/bin/env python3
"""
Circuit Breaker Manager - Gold Tier Core Component
===================================================

Centralized circuit breaker management for all system components.
Provides consistent failure handling and automatic recovery.

Features:
- Component-level circuit breakers
- Configurable failure thresholds
- Automatic state transitions (closed -> open -> half-open)
- Event emission for monitoring
- State persistence via StateManager
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum
from threading import Lock


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerManager:
    """
    Centralized circuit breaker management.

    Manages circuit breakers for all system components, providing
    consistent failure handling and automatic recovery.
    """

    def __init__(self, logger: logging.Logger, event_bus=None, state_manager=None,
                 failure_threshold: int = 5, recovery_timeout: int = 300):
        """
        Initialize CircuitBreakerManager.

        Args:
            logger: Logger instance
            event_bus: EventBus for event emission (optional)
            state_manager: StateManager for state persistence (optional)
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery (half-open)
        """
        self.logger = logger
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.lock = Lock()

        # Load state from StateManager if available
        self._load_state()

        self.logger.info(f"CircuitBreakerManager initialized (threshold={failure_threshold}, timeout={recovery_timeout}s)")

    def _load_state(self):
        """Load circuit breaker state from StateManager"""
        if self.state_manager:
            breakers_state = self.state_manager.get_system_state('circuit_breakers')
            if breakers_state:
                self.logger.info(f"Loaded {len(breakers_state)} circuit breaker states")
                return

        self.logger.debug("No persisted circuit breaker state found, starting fresh")

    def _get_breaker_state(self, component: str) -> Dict:
        """Get circuit breaker state for component from StateManager"""
        if self.state_manager:
            breakers = self.state_manager.get_system_state('circuit_breakers') or {}
            return breakers.get(component, self._create_default_breaker())
        return self._create_default_breaker()

    def _set_breaker_state(self, component: str, breaker: Dict):
        """Set circuit breaker state for component in StateManager"""
        if self.state_manager:
            breakers = self.state_manager.get_system_state('circuit_breakers') or {}
            breakers[component] = breaker
            self.state_manager.set_system_state('circuit_breakers', breakers)

    def _create_default_breaker(self) -> Dict:
        """Create default circuit breaker state"""
        return {
            'state': CircuitState.CLOSED.value,
            'failures': 0,
            'last_failure': None,
            'next_retry': None
        }

    def check_breaker(self, component: str) -> bool:
        """
        Check if circuit breaker allows execution.

        Args:
            component: Component name

        Returns:
            True if execution is allowed, False if circuit is open
        """
        with self.lock:
            breaker = self._get_breaker_state(component)

            if breaker['state'] == CircuitState.OPEN.value:
                # Check if we should try half-open
                if breaker['next_retry']:
                    next_retry = datetime.fromisoformat(breaker['next_retry'].replace('Z', '+00:00'))
                    if datetime.utcnow() >= next_retry.replace(tzinfo=None):
                        breaker['state'] = CircuitState.HALF_OPEN.value
                        self._set_breaker_state(component, breaker)

                        self.logger.info(f"Circuit breaker for {component} moving to HALF_OPEN")
                        self._emit_event('circuit_breaker_half_open', component, breaker)
                        return True

                return False

            return True

    def record_success(self, component: str):
        """
        Record successful execution.

        Args:
            component: Component name
        """
        with self.lock:
            breaker = self._get_breaker_state(component)

            if breaker['failures'] > 0:
                self.logger.info(f"Circuit breaker reset for {component} (was {breaker['failures']} failures)")

            breaker['failures'] = 0
            breaker['state'] = CircuitState.CLOSED.value
            breaker['next_retry'] = None

            self._set_breaker_state(component, breaker)

            if breaker['failures'] > 0:  # Only emit if recovering
                self._emit_event('circuit_breaker_closed', component, breaker)

    def record_failure(self, component: str):
        """
        Record failed execution.

        Args:
            component: Component name
        """
        with self.lock:
            breaker = self._get_breaker_state(component)
            breaker['failures'] += 1
            breaker['last_failure'] = datetime.utcnow().isoformat() + 'Z'

            # Open circuit after threshold failures
            if breaker['failures'] >= self.failure_threshold and breaker['state'] == CircuitState.CLOSED.value:
                breaker['state'] = CircuitState.OPEN.value
                next_retry = datetime.utcnow() + timedelta(seconds=self.recovery_timeout)
                breaker['next_retry'] = next_retry.isoformat() + 'Z'

                self.logger.error(f"Circuit breaker OPENED for {component} after {breaker['failures']} failures")
                self._emit_event('circuit_breaker_opened', component, breaker)

            self._set_breaker_state(component, breaker)

    def get_breaker_status(self, component: str) -> Dict:
        """
        Get circuit breaker status for component.

        Args:
            component: Component name

        Returns:
            Circuit breaker status dictionary
        """
        with self.lock:
            return self._get_breaker_state(component).copy()

    def get_all_breakers(self) -> Dict[str, Dict]:
        """
        Get all circuit breaker states.

        Returns:
            Dictionary of component -> breaker state
        """
        if self.state_manager:
            return self.state_manager.get_system_state('circuit_breakers') or {}
        return {}

    def reset_breaker(self, component: str):
        """
        Manually reset circuit breaker.

        Args:
            component: Component name
        """
        with self.lock:
            breaker = self._create_default_breaker()
            self._set_breaker_state(component, breaker)

            self.logger.info(f"Circuit breaker manually reset for {component}")
            self._emit_event('circuit_breaker_reset', component, breaker)

    def _emit_event(self, event_type: str, component: str, breaker: Dict):
        """Emit circuit breaker event"""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, {
                    'component': component,
                    'state': breaker['state'],
                    'failures': breaker['failures'],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
            except Exception as e:
                self.logger.error(f"Failed to emit circuit breaker event: {e}")
