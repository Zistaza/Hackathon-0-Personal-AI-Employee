#!/usr/bin/env python3
"""
AutonomousExecutor Integration Guide
=====================================

This file provides the exact changes needed to integrate the new
Gold Tier core components into autonomous_executor_hardened.py.

CHANGES REQUIRED:
1. Add imports for new core components
2. Update __init__ to accept CircuitBreakerManager
3. Replace internal circuit breaker with CircuitBreakerManager calls
4. Replace internal parsing with SocialMediaConfigParser calls
5. Replace internal state dicts with StateManager calls
6. Remove obsolete methods

APPROACH: Apply these changes incrementally and test after each section.
"""

# ============================================================================
# SECTION 1: IMPORTS (Add at top of file, after existing imports)
# ============================================================================

"""
ADD THESE IMPORTS after line 24 (after existing imports):

from Skills.integration_orchestrator.core import (
    CircuitBreakerManager,
    SocialMediaConfigParser
)
"""

# ============================================================================
# SECTION 2: UPDATE __init__ SIGNATURE (Line 1490)
# ============================================================================

"""
FIND (line 1490):
    def __init__(self, event_bus: EventBus, retry_queue: RetryQueue,
                 state_manager: StateManager, health_monitor: HealthMonitor,
                 skill_registry: 'SkillRegistry', audit_logger: AuditLogger,
                 base_dir: Path, logger: logging.Logger,
                 check_interval: int = 30, failure_threshold: int = 3):

REPLACE WITH:
    def __init__(self, event_bus: EventBus, retry_queue: RetryQueue,
                 state_manager: StateManager, health_monitor: HealthMonitor,
                 skill_registry: 'SkillRegistry', audit_logger: AuditLogger,
                 base_dir: Path, logger: logging.Logger,
                 circuit_breaker_manager: CircuitBreakerManager,
                 check_interval: int = 30, failure_threshold: int = 3):
"""

# ============================================================================
# SECTION 3: INITIALIZE COMPONENTS (In __init__, around line 1510-1530)
# ============================================================================

"""
FIND (around line 1520-1530):
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.state_manager = state_manager
        self.health_monitor = health_monitor
        self.skill_registry = skill_registry
        self.audit_logger = audit_logger
        self.base_dir = base_dir
        self.logger = logger
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold

ADD AFTER:
        # Gold Tier core components
        self.circuit_breaker_manager = circuit_breaker_manager
        self.social_parser = SocialMediaConfigParser(self.logger)

THEN FIND AND DELETE (around line 274-287):
        # Circuit breaker state
        self.circuit_breakers: Dict[str, Dict] = defaultdict(lambda: {
            'failures': 0,
            'last_failure': None,
            'state': 'closed',  # closed, open, half_open
            'next_retry': None
        })

        # Initialize parent tracking
        self.social_processed_files: Dict[str, datetime] = {}
        self.social_lock = Lock()

REPLACE WITH:
        # State lock for thread safety
        self.social_lock = Lock()
"""

# ============================================================================
# SECTION 4: REPLACE CIRCUIT BREAKER CALLS
# ============================================================================

"""
FIND ALL INSTANCES (multiple locations):
    if self._is_circuit_open(component):

REPLACE WITH:
    if not self.circuit_breaker_manager.check_breaker(component):

---

FIND ALL INSTANCES:
    self._record_circuit_failure(component)

REPLACE WITH:
    self.circuit_breaker_manager.record_failure(component)

---

FIND ALL INSTANCES:
    self._reset_circuit_breaker(component)

REPLACE WITH:
    self.circuit_breaker_manager.record_success(component)

---

SPECIFIC LOCATIONS:
- Line 312: if self._is_circuit_open('social_media_check'):
- Line 336: self._reset_circuit_breaker('social_media_check')
- Line 345: self._record_circuit_failure('social_media_check')
- Line 500: if self._is_circuit_open(platform):
- Line 584: self._reset_circuit_breaker(platform)
- Line 613: self._record_circuit_failure(platform)
"""

# ============================================================================
# SECTION 5: REPLACE PARSING CALLS
# ============================================================================

"""
FIND (line 368):
    social_config = self._parse_social_media_config(filepath)

REPLACE WITH:
    social_config = self.social_parser.parse(filepath)

---

FIND (line 405):
    social_config = self._parse_social_media_config(filepath)

REPLACE WITH:
    social_config = self.social_parser.parse(filepath)

---

FIND (line 414):
    scheduled_time = self._parse_scheduled_time(social_config['scheduled_time'])

REPLACE WITH:
    scheduled_time = self.social_parser.parse_scheduled_time(social_config['scheduled_time'])

---

FIND (line 470):
    message = self._extract_message_from_content(filepath)

REPLACE WITH:
    message = self.social_parser.extract_message_from_content(filepath)
"""

# ============================================================================
# SECTION 6: REPLACE STATE ACCESS - social_processed_files
# ============================================================================

"""
FIND (line 849-856):
    def _is_recently_processed(self, filepath: Path) -> bool:
        \"\"\"Check if file was recently processed\"\"\"
        with self.social_lock:
            last_processed = self.social_processed_files.get(str(filepath))
            if last_processed:
                if (datetime.utcnow() - last_processed) < timedelta(hours=1):
                    return True
        return False

REPLACE WITH:
    def _is_recently_processed(self, filepath: Path) -> bool:
        \"\"\"Check if file was recently processed\"\"\"
        with self.social_lock:
            processed_files = self.state_manager.get_system_state('social_processed_files') or {}
            last_processed = processed_files.get(str(filepath))
            if last_processed:
                last_time = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
                if (datetime.utcnow() - last_time.replace(tzinfo=None)) < timedelta(hours=1):
                    return True
        return False

---

FIND (line 858-868):
    def _mark_as_processed(self, filepath: Path):
        \"\"\"Mark file as processed\"\"\"
        with self.social_lock:
            self.social_processed_files[str(filepath)] = datetime.utcnow()

            # Clean up old entries (older than 24 hours)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            self.social_processed_files = {
                k: v for k, v in self.social_processed_files.items()
                if v > cutoff
            }

REPLACE WITH:
    def _mark_as_processed(self, filepath: Path):
        \"\"\"Mark file as processed\"\"\"
        with self.social_lock:
            processed_files = self.state_manager.get_system_state('social_processed_files') or {}
            processed_files[str(filepath)] = datetime.utcnow().isoformat() + 'Z'

            # Clean up old entries (older than 24 hours)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            processed_files = {
                k: v for k, v in processed_files.items()
                if datetime.fromisoformat(v.replace('Z', '+00:00')).replace(tzinfo=None) > cutoff
            }

            self.state_manager.set_system_state('social_processed_files', processed_files)
"""

# ============================================================================
# SECTION 7: REPLACE STATE ACCESS - task_failure_counts
# ============================================================================

"""
FIND (line 876-878):
    with self.social_lock:
        self.task_failure_counts[tracking_key] = \\
            self.task_failure_counts.get(tracking_key, 0) + 1
        failure_count = self.task_failure_counts[tracking_key]

REPLACE WITH:
    with self.social_lock:
        failure_counts = self.state_manager.get_system_state('task_failure_counts') or {}
        failure_counts[tracking_key] = failure_counts.get(tracking_key, 0) + 1
        failure_count = failure_counts[tracking_key]
        self.state_manager.set_system_state('task_failure_counts', failure_counts)

---

FIND (line 587-589):
    with self.social_lock:
        if tracking_key in self.task_failure_counts:
            del self.task_failure_counts[tracking_key]

REPLACE WITH:
    with self.social_lock:
        failure_counts = self.state_manager.get_system_state('task_failure_counts') or {}
        if tracking_key in failure_counts:
            del failure_counts[tracking_key]
            self.state_manager.set_system_state('task_failure_counts', failure_counts)
"""

# ============================================================================
# SECTION 8: DELETE OBSOLETE METHODS
# ============================================================================

"""
DELETE THESE ENTIRE METHODS (lines 625-660, 666-847):

1. _is_circuit_open() - Line 625-637
2. _record_circuit_failure() - Line 639-650
3. _reset_circuit_breaker() - Line 652-660
4. _parse_social_media_config() - Line 666-697
5. _parse_yaml_frontmatter() - Line 699-742
6. _parse_inline_markers() - Line 744-775
7. _parse_json_block() - Line 777-789
8. _parse_scheduled_time() - Line 791-805
9. _extract_message_from_content() - Line 819-847

These methods are now provided by CircuitBreakerManager and SocialMediaConfigParser.
"""

# ============================================================================
# SECTION 9: UPDATE ORCHESTRATOR INSTANTIATION
# ============================================================================

"""
In Skills/integration_orchestrator/index.py (line ~2053):

FIND:
    self.autonomous_executor = AutonomousExecutor(
        event_bus=self.event_bus,
        retry_queue=self.retry_queue,
        state_manager=self.state_manager,
        health_monitor=self.health_monitor,
        skill_registry=self.skill_registry,
        audit_logger=self.audit_logger,
        base_dir=self.base_dir,
        logger=self.logger,
        check_interval=30,
        failure_threshold=3
    )

REPLACE WITH:
    self.autonomous_executor = AutonomousExecutor(
        event_bus=self.event_bus,
        retry_queue=self.retry_queue,
        state_manager=self.state_manager,
        health_monitor=self.health_monitor,
        skill_registry=self.skill_registry,
        audit_logger=self.audit_logger,
        base_dir=self.base_dir,
        logger=self.logger,
        circuit_breaker_manager=self.circuit_breaker_manager,  # ADD THIS LINE
        check_interval=30,
        failure_threshold=3
    )
"""

# ============================================================================
# TESTING CHECKLIST
# ============================================================================

"""
After applying all changes, test:

1. System starts without errors
2. Social media detection works
3. Circuit breakers trigger correctly
4. State persists in state.json:
   - Check for 'circuit_breakers' key
   - Check for 'social_processed_files' key
   - Check for 'task_failure_counts' key
5. Restart system and verify state is restored
6. Check audit logs for correct execution
7. Verify no behavioral changes

If any test fails, review the specific section and verify the changes were applied correctly.
"""

print("AutonomousExecutor Integration Guide loaded.")
print("Apply changes in order: Sections 1-9")
print("Test after each section if possible.")
