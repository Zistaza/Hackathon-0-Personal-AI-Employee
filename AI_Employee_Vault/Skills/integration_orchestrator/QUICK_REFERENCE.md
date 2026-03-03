# Enterprise Social Media Skills - Quick Reference

## 🚀 Quick Start

### Basic Post with Enterprise Features
```python
result = orchestrator.social_adapter.post(
    platform='facebook',
    message='Your content here',
    media=['image.jpg'],  # optional
    metadata={'campaign': 'spring_2026'}  # optional
)

# Returns:
# - success: bool
# - post_id: str
# - engagement: {likes, comments, shares, reach, engagement_rate}
# - moderation: {risk_score, risk_level, approved}
# - validation: {valid, issues}
```

### Schedule a Post
```python
from datetime import datetime, timedelta

result = orchestrator.social_adapter.schedule_post(
    platform='instagram',
    message='Scheduled content',
    scheduled_time=datetime.utcnow() + timedelta(hours=2),
    media=['photo.jpg']
)

# Automatically executes via PeriodicTrigger
```

### Get Analytics
```python
summary = orchestrator.social_adapter.get_analytics_summary()

# Returns:
# {
#   'overall': {total_posts, total_reach, avg_engagement_rate},
#   'platforms': {facebook: {...}, instagram: {...}, twitter_x: {...}}
# }
```

## 🛡️ Enterprise Features

| Feature | Status | Description |
|---------|--------|-------------|
| Content Validation | ✅ | Blocks prohibited words, validates length |
| Content Moderation | ✅ | Risk scoring (0-1), auto-blocks high-risk |
| Engagement Tracking | ✅ | Simulated metrics per platform |
| Post Scheduling | ✅ | State-based, auto-execution |
| Social Analytics | ✅ | Weekly summaries, aggregation |
| Centralized Retry | ✅ | Uses RetryQueue, exponential backoff |

## 📊 Prohibited Words List

`spam`, `scam`, `fake`, `illegal`, `hack`, `exploit`, `violence`, `hate`, `discrimination`, `offensive`

## 🎯 Risk Scoring

- **0.0-0.3**: LOW (approved)
- **0.3-0.5**: MEDIUM (approved)
- **0.5-0.7**: HIGH (approved)
- **0.7-1.0**: CRITICAL (blocked)

Default threshold: 0.7

## 📁 State.json Keys

```
scheduled_posts                    # All scheduled posts
engagement_{platform}_{post_id}    # Engagement metrics
social_analytics_weekly            # Weekly summary
successful_posts_{platform}        # Success counter
failed_posts_{platform}            # Failure counter
total_posts_{platform}             # Total counter
```

## 🔔 Events Emitted

- `social_post_success` - Post published successfully
- `social_post_failed` - Post failed
- `social_post_scheduled` - Post scheduled for future
- `scheduled_post_executed` - Scheduled post executed
- `content_moderation` - Content blocked by moderation

## 📝 Platform Limits

| Platform | Character Limit | Media Limit |
|----------|----------------|-------------|
| Facebook | 63,206 | 10 items |
| Instagram | 2,200 | 10 items (required) |
| Twitter/X | 280 | 4 items |

## 🧪 Testing

```bash
# Validate features
python3 validate_enterprise.py

# Run full test suite (requires full setup)
python3 test_enterprise_social.py

# Run usage examples
python3 enterprise_social_examples.py
```

## 📚 Documentation

- `ENTERPRISE_DELIVERY_SUMMARY.md` - Complete delivery report
- `ENTERPRISE_SOCIAL_MEDIA_README.md` - Full feature documentation
- `enterprise_social_examples.py` - 10 practical examples
- `test_enterprise_social.py` - Comprehensive test suite

## ✅ Compliance

- ✅ Only modified social_media_skills.py
- ✅ No core infrastructure changes
- ✅ No duplication (uses EventBus, RetryQueue, StateManager)
- ✅ Modular and production-safe
- ✅ Thread-safe operations
- ✅ Full audit trail

## 🎉 Version

**2.0.0 - Enterprise Edition**

Upgrade Date: 2026-03-01
