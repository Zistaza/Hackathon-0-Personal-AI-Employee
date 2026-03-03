# Facebook Post Skill - Enterprise Edition

Standalone Agent Skill for posting to Facebook with enterprise-grade features.

## Features

- ✅ **Content Validation**: Character limits, prohibited words, spam detection
- ✅ **Content Moderation**: Risk scoring with configurable thresholds
- ✅ **Engagement Tracking**: Simulated metrics (likes, comments, shares, reach)
- ✅ **Idempotent Execution**: Prevents duplicate posts
- ✅ **Audit Logging**: Structured event logging for compliance
- ✅ **Report Generation**: Detailed markdown reports for each post
- ✅ **Retry Logic**: Automatic retry with exponential backoff
- ✅ **Event Bus Integration**: Publishes events for orchestration

## Installation

This skill is part of the AI Employee Vault and requires the integration orchestrator:

```bash
cd Skills/facebook_post_skill
# No additional dependencies required - uses shared components
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "platform": "facebook",
  "api": {
    "simulation_mode": true,
    "success_rate": 0.95
  },
  "validation": {
    "max_length": 63206,
    "max_media": 10
  },
  "moderation": {
    "threshold": 0.5
  }
}
```

## Usage

### Standalone CLI

```bash
# Simple post
python index.py "Your post message here"

# Post with media
python index.py "Check out this image!" --media path/to/image.jpg

# Test mode
python index.py --test

# Dry run
python index.py "Test message" --dry-run
```

### Programmatic Usage

```python
from Skills.facebook_post_skill.index import execute

result = execute(
    message="Hello from Facebook skill!",
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

### `execute(message, media=None, metadata=None, ...)`

Main entry point for posting to Facebook.

**Parameters:**
- `message` (str): Post content (max 63,206 characters)
- `media` (List[str], optional): List of media file paths or URLs (max 10)
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
    'platform': 'facebook',
    'timestamp': str,
    'engagement': {
        'likes': int,
        'comments': int,
        'shares': int,
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
- Message cannot be empty
- Maximum 63,206 characters
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

Generated reports are saved to `Reports/Social/Facebook/`:

```
facebook_post_20260302_143022.md
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

The skill handles errors gracefully:

1. **Validation Errors**: Returns error with validation details
2. **Moderation Blocks**: Returns error with risk analysis
3. **API Failures**: Automatically retries with exponential backoff
4. **Unexpected Errors**: Logs error and returns failure status

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
facebook_post_skill/
├── index.py              # Main skill implementation
├── skill.json            # Skill metadata
├── config.json           # Configuration
├── README.md             # This file
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

To use with real Facebook API:

1. Update `config.json`:
   ```json
   {
     "api": {
       "simulation_mode": false,
       "access_token": "YOUR_TOKEN",
       "page_id": "YOUR_PAGE_ID"
     }
   }
   ```

2. Implement real API calls in `_simulate_post()` method
3. Add Facebook SDK dependency
4. Configure OAuth authentication

## License

Part of AI Employee Vault - Enterprise Edition

## Support

For issues or questions, refer to the main project documentation.
