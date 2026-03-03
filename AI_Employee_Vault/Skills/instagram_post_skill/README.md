# Instagram Post Skill - Enterprise Edition

Standalone Agent Skill for posting to Instagram with enterprise-grade features.

## Features

- ✅ **Content Validation**: Caption limits, media requirements, prohibited words
- ✅ **Content Moderation**: Risk scoring with configurable thresholds
- ✅ **Engagement Tracking**: Simulated metrics (likes, comments, saves, reach)
- ✅ **Idempotent Execution**: Prevents duplicate posts
- ✅ **Audit Logging**: Structured event logging for compliance
- ✅ **Report Generation**: Detailed markdown reports for each post
- ✅ **Retry Logic**: Automatic retry with exponential backoff
- ✅ **Event Bus Integration**: Publishes events for orchestration

## Instagram-Specific Requirements

Instagram has unique requirements compared to other platforms:
- **Media Required**: At least 1 media item (image or video)
- **Caption Limit**: Maximum 2,200 characters
- **Carousel Limit**: Maximum 10 media items per post

## Installation

This skill is part of the AI Employee Vault and requires the integration orchestrator:

```bash
cd Skills/instagram_post_skill
# No additional dependencies required - uses shared components
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "platform": "instagram",
  "api": {
    "simulation_mode": true,
    "success_rate": 0.93
  },
  "validation": {
    "max_length": 2200,
    "max_media": 10,
    "min_media": 1
  },
  "moderation": {
    "threshold": 0.5
  }
}
```

## Usage

### Standalone CLI

```bash
# Post with single image
python index.py "Your caption here" --media path/to/image.jpg

# Post with multiple images (carousel)
python index.py "Check out these photos!" --media img1.jpg img2.jpg img3.jpg

# Test mode
python index.py --test

# Using run script
./run.sh "Beautiful sunset 🌅" --media sunset.jpg
```

### Programmatic Usage

```python
from Skills.instagram_post_skill.index import execute

result = execute(
    message="Hello from Instagram skill! 📸",
    media=["path/to/image.jpg"],
    metadata={"campaign": "launch"}
)

if result['success']:
    print(f"Posted: {result['url']}")
    print(f"Engagement: {result['engagement']}")
```

### Integration with Orchestrator

The skill is automatically registered with the integration orchestrator:

```python
from Skills.integration_orchestrator.index import IntegrationOrchestrator

orchestrator = IntegrationOrchestrator(base_dir)
orchestrator.start()

# Skill is triggered by events or manual execution
```

## API Reference

### `execute(message, media, metadata=None, ...)`

Main entry point for posting to Instagram.

**Parameters:**
- `message` (str): Post caption (max 2,200 characters)
- `media` (List[str], **required**): List of media file paths or URLs (1-10 items)
- `metadata` (Dict, optional): Additional metadata for tracking
- `event_bus` (EventBus, optional): For event emission
- `audit_logger` (AuditLogger, optional): For audit logging
- `retry_queue` (RetryQueue, optional): For retry logic
- `state_manager` (StateManager, optional): For state persistence

**Returns:**
```python
{
    'success': bool,
    'post_id': str,
    'url': str,
    'platform': 'instagram',
    'timestamp': str,
    'engagement': {
        'likes': int,
        'comments': int,
        'saves': int,
        'reach': int,
        'engagement_rate': float
    },
    'moderation': {
        'risk_score': float,
        'risk_level': str,
        'approved': bool
    }
}
```

## Validation Rules

### Content Validation
- Caption cannot be empty
- Maximum 2,200 characters
- **Minimum 1 media item (required)**
- Maximum 10 media items
- Checks for prohibited words
- Detects excessive capitalization (spam)
- Detects excessive special characters

### Content Moderation
- Risk scoring based on content analysis
- Blocks posts with risk score > 0.5 (configurable)
- Factors: marketing keywords, URLs, punctuation, length
- Risk levels: LOW, MEDIUM, HIGH, CRITICAL

## Reports

Generated reports are saved to `Reports/Social/Instagram/`:

```
instagram_post_20260302_143022.md
```

Each report includes:
- Execution details
- Post information (ID, URL, timestamp)
- Content and media
- Validation results
- Moderation analysis
- Engagement metrics
- Performance data

## Events

The skill publishes these events:

- `social_post_success`: Post succeeded
- `social_post_failed`: Post failed
- `content_blocked`: Content blocked by moderation

## Error Handling

Common errors and solutions:

1. **Missing Media**: Instagram requires at least one media item
   - Solution: Always provide `--media` parameter

2. **Caption Too Long**: Maximum 2,200 characters
   - Solution: Shorten your caption

3. **Too Many Media Items**: Maximum 10 items
   - Solution: Reduce number of media files

## Testing

```bash
# Run test mode
python index.py --test

# Expected output:
# ✓ Content validation passed
# ✓ Moderation approved (risk: LOW)
# ✓ Post successful
# ✓ Engagement metrics generated
# ✓ Report created
```

## Architecture

```
instagram_post_skill/
├── index.py              # Main skill implementation
├── skill.json            # Skill metadata
├── config.json           # Configuration
├── README.md             # This file
├── run.sh                # Startup script
└── .gitignore           # Git ignore rules

Shared Components (from integration_orchestrator):
├── social_media_common.py
    ├── BaseSocialSkill      # Abstract base class
    ├── ContentValidator     # Validation logic
    ├── ContentModerator     # Moderation logic
    ├── EngagementTracker    # Metrics generation
    └── SocialAnalytics      # Analytics aggregation
```

## Dependencies

- Python 3.8+
- integration_orchestrator (shared components)
- No external API dependencies (simulation mode)

## Production Deployment

To use with real Instagram API:

1. Update `config.json`:
   ```json
   {
     "api": {
       "simulation_mode": false,
       "access_token": "YOUR_TOKEN",
       "instagram_account_id": "YOUR_ACCOUNT_ID"
     }
   }
   ```

2. Implement real API calls in `_simulate_post()` method
3. Add Instagram SDK dependency
4. Configure OAuth authentication

## License

Part of AI Employee Vault - Enterprise Edition
