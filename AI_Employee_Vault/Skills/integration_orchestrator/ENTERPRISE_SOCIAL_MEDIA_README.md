# Social Media Skills - Enterprise Edition

## Overview

The social media skills have been upgraded to **Enterprise Mode** with advanced features for production-grade social media automation.

## Enterprise Features Implemented

### 1. Content Validation ✓
- **Prohibited Words Checking**: Blocks content containing blacklisted terms
- **Length Validation**: Platform-specific character limits
- **Spam Detection**: Identifies excessive capitalization and special characters
- **Structured Reports**: Detailed validation results with severity levels

**Example:**
```python
validator = ContentValidator(logger)
result = validator.validate("Check out our product!", "facebook")
# Returns: {'valid': True/False, 'issues': [...], 'validated_at': '...'}
```

### 2. Content Moderation ✓
- **Risk Scoring**: 0.0-1.0 risk score based on content analysis
- **Risk Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Automatic Blocking**: Rejects content above threshold (default: 0.7)
- **Risk Factors**: Detailed explanation of why content was flagged

**Risk Factors Analyzed:**
- Marketing keywords (buy now, click here, limited time)
- URL presence
- Excessive punctuation
- Message length anomalies

**Example:**
```python
moderator = ContentModerator(logger, threshold=0.7)
result = moderator.moderate("Great product announcement!")
# Returns: {'approved': True/False, 'risk_score': 0.15, 'risk_level': 'low', ...}
```

### 3. Engagement Tracking ✓
- **Simulated Metrics**: Realistic engagement data for testing
- **Platform-Specific**: Different metrics per platform
- **State Persistence**: Metrics stored in state.json via StateManager
- **Aggregate Tracking**: Counters for total posts per platform

**Metrics Generated:**
- **Facebook**: likes, comments, shares, reach, engagement_rate
- **Instagram**: likes, comments, saves, reach, engagement_rate
- **Twitter/X**: likes, retweets, replies, views, engagement_rate

**Example:**
```python
tracker = EngagementTracker(logger, state_manager)
metrics = tracker.generate_metrics('facebook', 'post_123', 'content')
# Returns: {'likes': 245, 'comments': 18, 'shares': 12, 'reach': 3421, ...}
```

### 4. Post Scheduling ✓
- **State-Based Storage**: Scheduled posts stored in state.json
- **PeriodicTrigger Integration**: Automatic execution every minute
- **Event Emission**: `scheduled_post_executed` event on completion
- **Status Tracking**: SCHEDULED → POSTED/FAILED

**Example:**
```python
# Schedule a post
result = adapter.schedule_post(
    platform='facebook',
    message='Future post content',
    scheduled_time=datetime.utcnow() + timedelta(hours=2),
    media=['image.jpg']
)

# PeriodicTrigger automatically executes when time arrives
# Or manually trigger: adapter.execute_scheduled_posts()
```

### 5. Social Analytics ✓
- **Weekly Summaries**: Aggregated metrics across all platforms
- **Platform Breakdown**: Individual platform performance
- **Overall Metrics**: Total posts, reach, engagement rates
- **State Persistence**: Analytics stored for historical tracking

**Example:**
```python
summary = adapter.get_analytics_summary()
# Returns:
# {
#   'period': 'weekly',
#   'overall': {'total_posts': 15, 'total_reach': 45000, 'avg_engagement_rate': 3.2},
#   'platforms': {
#     'facebook': {'total_posts': 5, 'avg_engagement_rate': 3.5, ...},
#     'instagram': {...},
#     'twitter_x': {...}
#   }
# }
```

### 6. Centralized Retry Logic ✓
- **No Internal Retries**: All retry logic handled by centralized RetryQueue
- **Exponential Backoff**: Managed externally by orchestrator
- **Max 3 Attempts**: Configurable retry limit
- **Context Preservation**: Full metadata preserved across retries

## Architecture Compliance

### ✓ No Modifications to Core Infrastructure
- EventBus: Used for event emission only
- RetryQueue: Used for centralized retry only
- StateManager: Used for persistence only
- CircuitBreakerManager: Not modified
- SkillRegistry: Not modified
- Folder structure: Unchanged

### ✓ No Duplication
- No custom retry logic (uses RetryQueue)
- No custom scheduling (uses PeriodicTrigger)
- No custom state management (uses StateManager)
- No custom event system (uses EventBus)

### ✓ Modular Design
- All enterprise features in social_media_skills.py
- Clean separation of concerns
- Backward compatible with existing code
- Easy to test and maintain

## Integration Points

### 1. Orchestrator Integration
```python
# In index.py
self.social_adapter = register_social_skills(
    skill_registry=self.skill_registry,
    logger=self.logger,
    event_bus=self.event_bus,
    audit_logger=self.audit_logger,
    retry_queue=self.retry_queue,
    reports_dir=reports_dir,
    state_manager=self.state_manager  # Enterprise
)

# Connect to PeriodicTrigger
self.periodic_trigger.social_adapter = self.social_adapter
```

### 2. PeriodicTrigger Integration
```python
# In periodic_trigger.py
if self.social_adapter:
    result = self.social_adapter.execute_scheduled_posts()
    # Executes every minute automatically
```

### 3. State Persistence
```python
# Scheduled posts stored in state.json
{
  "scheduled_posts": {
    "abc123": {
      "platform": "facebook",
      "message": "...",
      "scheduled_time": "2026-03-01T15:00:00",
      "status": "scheduled"
    }
  },
  "engagement_facebook_post_123": {
    "likes": 245,
    "engagement_rate": 3.2
  },
  "social_analytics_weekly": {
    "period": "weekly",
    "overall": {...}
  }
}
```

## Event Flow

### Successful Post
1. `execute()` → Content validation
2. Content moderation (risk scoring)
3. Platform-specific validation
4. Simulate API post
5. Generate engagement metrics
6. Emit `social_post_success` event
7. Audit log entry
8. Generate enterprise report
9. Update state metrics

### Failed Post
1. Validation/moderation failure
2. Emit `social_post_failed` event
3. Audit log entry
4. Enqueue to RetryQueue (centralized)
5. Update failure metrics

### Scheduled Post
1. `schedule_post()` → Store in state.json
2. Emit `social_post_scheduled` event
3. PeriodicTrigger checks every minute
4. Execute when time arrives
5. Emit `scheduled_post_executed` event
6. Update status in state.json

## Testing

Run the comprehensive test suite:
```bash
cd Skills/integration_orchestrator
python test_enterprise_social.py
```

Tests cover:
- Content validation with prohibited words
- Content moderation with risk scoring
- Engagement tracking simulation
- Post scheduling and execution
- Social analytics generation
- Full enterprise workflow

## Reports Generated

Enterprise reports include:
- Execution details
- Content validation results
- Content moderation analysis
- Engagement metrics
- Performance data

Location: `Reports/Social/[platform]_post_[timestamp].md`

## Version

**Version**: 2.0.0 (Enterprise Edition)

**Upgrade Date**: 2026-03-01

**Features Added**:
- content_validation
- content_moderation
- engagement_tracking
- post_scheduling
- analytics

## Production Safety

✓ **Thread-Safe**: All state operations use locks
✓ **Idempotent**: Content hashing prevents duplicates
✓ **Graceful Degradation**: Optional components (state_manager, event_bus)
✓ **Error Handling**: Comprehensive try-catch blocks
✓ **Audit Trail**: All actions logged via AuditLogger
✓ **Event-Driven**: Loose coupling via EventBus
✓ **Retry Logic**: Centralized via RetryQueue
✓ **State Persistence**: All data survives restarts

## Future Enhancements

Potential additions (not implemented):
- Real API integration (currently simulated)
- Advanced scheduling (cron expressions)
- A/B testing support
- Multi-account management
- Content templates
- Approval workflows
- Performance analytics dashboard
