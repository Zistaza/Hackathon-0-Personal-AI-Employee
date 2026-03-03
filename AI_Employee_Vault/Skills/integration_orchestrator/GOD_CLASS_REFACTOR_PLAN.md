# God Class Refactoring - Migration Plan

**Date:** 2026-03-01
**Target File:** `index.py` (2,633 lines)
**Goal:** Extract components into modular structure (~200-400 lines remaining)
**Risk Level:** 🔴 HIGH - Core system refactoring
**Estimated Effort:** 2-3 hours (with careful testing)

---

## PHASE 1: PREPARATION

### Current State Analysis

**File:** `Skills/integration_orchestrator/index.py`
- **Total Lines:** 2,633
- **Components:** 15+ classes in single file
- **Dependencies:** Complex interdependencies
- **Risk:** High coupling, difficult to test

### Target State

**File Structure:**
```
Skills/integration_orchestrator/
├── core/
│   ├── __init__.py
│   ├── event_bus.py          (EventBus)
│   ├── retry_queue.py         (RetryQueue, RetryPolicy)
│   ├── health_monitor.py      (HealthMonitor, ComponentStatus)
│   ├── audit_logger.py        (AuditLogger)
│   ├── state_manager.py       (StateManager)
│   ├── approval_manager.py    (ApprovalManager)
│   └── circuit_breaker.py     (CircuitBreakerManager) [already exists]
├── skills/
│   ├── __init__.py
│   ├── skill_dispatcher.py    (SkillDispatcher)
│   └── skill_registry.py      (SkillRegistry)
├── routing/
│   ├── __init__.py
│   ├── event_router.py        (EventRouter)
│   └── folder_watcher.py      (FolderWatcherHandler)
├── execution/
│   ├── __init__.py
│   ├── email_executor.py      (EmailExecutor)
│   ├── periodic_trigger.py    (PeriodicTrigger)
│   ├── graceful_degradation.py (GracefulDegradation)
│   └── autonomous_executor.py (AutonomousExecutor)
├── index.py                   (IntegrationOrchestrator only, ~300 lines)
├── social_media_skills.py     [existing]
├── mcp_core.py                [existing]
└── autonomous_executor_hardened.py [existing]
```

---

## PHASE 2: DEPENDENCY ANALYSIS

### Component Dependencies (Bottom-Up)

**Level 0: No Dependencies**
1. EventBus (logger only)
2. ComponentStatus (Enum)
3. RetryPolicy (Enum)

**Level 1: Minimal Dependencies**
4. StateManager (logger only)
5. ApprovalManager (logger only)
6. AuditLogger (logger only)

**Level 2: Core Infrastructure**
7. RetryQueue (logger)
8. HealthMonitor (logger)

**Level 3: Enhanced Components**
9. SkillDispatcher (logger, base_dir)
10. EmailExecutor (logger, base_dir)
11. PeriodicTrigger (logger)

**Level 4: Wrapper Components**
12. SkillRegistry (SkillDispatcher, EventBus, RetryQueue, AuditLogger, logger)
13. GracefulDegradation (HealthMonitor, logger)

**Level 5: Complex Components**
14. EventRouter (StateManager, ApprovalManager, SkillDispatcher, EmailExecutor, logger, base_dir)
15. FolderWatcherHandler (EventRouter, logger)
16. AutonomousExecutor (EventBus, RetryQueue, StateManager, HealthMonitor, SkillRegistry, AuditLogger, logger, base_dir)

**Level 6: Orchestrator**
17. IntegrationOrchestrator (all components)

---

## PHASE 3: EXTRACTION ORDER

### Step 1: Create Directory Structure
```bash
mkdir -p core skills routing execution
touch core/__init__.py skills/__init__.py routing/__init__.py execution/__init__.py
```

### Step 2: Extract Level 0-1 Components (Standalone)
1. ✅ `core/event_bus.py` - EventBus class
2. ✅ `core/retry_queue.py` - RetryQueue, RetryPolicy
3. ✅ `core/health_monitor.py` - HealthMonitor, ComponentStatus
4. ✅ `core/audit_logger.py` - AuditLogger
5. ✅ `core/state_manager.py` - StateManager
6. ✅ `core/approval_manager.py` - ApprovalManager

### Step 3: Extract Level 2-3 Components (Simple Dependencies)
7. ✅ `skills/skill_dispatcher.py` - SkillDispatcher
8. ✅ `execution/email_executor.py` - EmailExecutor
9. ✅ `execution/periodic_trigger.py` - PeriodicTrigger

### Step 4: Extract Level 4 Components (Wrapper)
10. ✅ `skills/skill_registry.py` - SkillRegistry
11. ✅ `execution/graceful_degradation.py` - GracefulDegradation

### Step 5: Extract Level 5 Components (Complex)
12. ✅ `routing/event_router.py` - EventRouter
13. ✅ `routing/folder_watcher.py` - FolderWatcherHandler
14. ✅ `execution/autonomous_executor.py` - AutonomousExecutor

### Step 6: Update IntegrationOrchestrator
15. ✅ Update `index.py` - Import all components, orchestrate only

---

## PHASE 4: IMPLEMENTATION STRATEGY

### Extraction Pattern (for each component)

```python
# 1. Create new file: core/component_name.py
#!/usr/bin/env python3
"""
Component Name
==============

Description of component purpose.
"""

import logging
from typing import ...
# Other imports

class ComponentName:
    """Component description"""

    def __init__(self, ...):
        """Initialize component"""
        # Implementation

    # Methods...
```

### Import Pattern (in index.py)

```python
# Old (before refactoring)
class EventBus:
    """Central pub/sub event bus"""
    # 40+ lines of implementation

# New (after refactoring)
from Skills.integration_orchestrator.core.event_bus import EventBus
```

---

## PHASE 5: BACKWARD COMPATIBILITY

### Maintain Public API

**Option 1: Re-export from index.py**
```python
# index.py
from Skills.integration_orchestrator.core.event_bus import EventBus
from Skills.integration_orchestrator.core.retry_queue import RetryQueue

# Re-export for backward compatibility
__all__ = ['IntegrationOrchestrator', 'EventBus', 'RetryQueue', ...]
```

**Option 2: Update imports in dependent files**
```python
# Before
from Skills.integration_orchestrator.index import EventBus

# After
from Skills.integration_orchestrator.core.event_bus import EventBus
```

**Recommendation:** Use Option 1 for backward compatibility, then gradually migrate to Option 2.

---

## PHASE 6: TESTING STRATEGY

### Unit Tests
- Test each extracted component independently
- Verify no functionality changes
- Test dependency injection

### Integration Tests
- Test IntegrationOrchestrator initialization
- Test component interactions
- Test event flow
- Test skill execution

### Regression Tests
- Run existing test suite
- Verify no behavior changes
- Check all imports resolve

---

## PHASE 7: RISK MITIGATION

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Import errors | 🔴 HIGH | Careful import management, test each file |
| Circular dependencies | 🔴 HIGH | Follow dependency order, use forward references |
| Missing dependencies | ⚠️ MEDIUM | Explicit dependency injection |
| Broken functionality | 🔴 HIGH | No logic changes, only moves |
| Test failures | ⚠️ MEDIUM | Run tests after each extraction |

### Rollback Plan
- Keep original index.py as index.py.backup
- Can revert by restoring backup
- Git commit after each successful extraction

---

## PHASE 8: EXECUTION CHECKLIST

### Pre-Refactoring
- [ ] Create backup of index.py
- [ ] Create directory structure
- [ ] Create __init__.py files
- [ ] Review dependency graph

### During Refactoring
- [ ] Extract Level 0-1 components (standalone)
- [ ] Extract Level 2-3 components (simple deps)
- [ ] Extract Level 4 components (wrappers)
- [ ] Extract Level 5 components (complex)
- [ ] Update index.py imports
- [ ] Update index.py to use imported components
- [ ] Remove extracted code from index.py

### Post-Refactoring
- [ ] Verify all imports resolve
- [ ] Run test suite
- [ ] Check file sizes
- [ ] Verify backward compatibility
- [ ] Update documentation

---

## PHASE 9: EXPECTED OUTCOMES

### File Size Reduction
```
Before:
index.py: 2,633 lines

After:
index.py: ~300 lines (orchestration only)
core/: ~800 lines (7 files)
skills/: ~200 lines (2 files)
routing/: ~400 lines (2 files)
execution/: ~900 lines (4 files)
Total: ~2,600 lines (distributed across 16 files)
```

### Maintainability Improvements
- ✅ Single Responsibility Principle
- ✅ Easier to test individual components
- ✅ Clearer dependencies
- ✅ Easier to modify components
- ✅ Better code organization

### Architectural Compliance
- ✅ No god class
- ✅ Modular structure
- ✅ Clear separation of concerns
- ✅ Dependency injection pattern
- ✅ Testable components

---

## PHASE 10: IMPLEMENTATION NOTES

### Import Management
```python
# Use absolute imports
from Skills.integration_orchestrator.core.event_bus import EventBus

# Not relative imports
from .core.event_bus import EventBus  # Avoid
```

### Dependency Injection
```python
# Good: Explicit dependencies
def __init__(self, event_bus: EventBus, logger: logging.Logger):
    self.event_bus = event_bus
    self.logger = logger

# Bad: Creating dependencies internally
def __init__(self):
    self.event_bus = EventBus(logger)  # Avoid
```

### Type Hints
```python
# Use forward references for circular dependencies
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Skills.integration_orchestrator.skills.skill_registry import SkillRegistry

def __init__(self, skill_registry: 'SkillRegistry'):
    ...
```

---

## READY TO PROCEED?

This migration plan provides:
- ✅ Clear extraction order
- ✅ Dependency analysis
- ✅ Risk mitigation strategy
- ✅ Testing approach
- ✅ Backward compatibility plan

**Estimated Time:** 2-3 hours for careful, systematic refactoring

**Next Step:** Execute Phase 1-2 (directory structure + extract standalone components)

---

**Approval Required:** This is a major refactoring. Confirm you want to proceed with execution.
