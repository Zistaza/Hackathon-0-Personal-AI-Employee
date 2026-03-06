# Social Media Executor v2

Unified social media posting executor with HITL (Human-in-the-Loop) workflow and persistent browser sessions.

## Features

- **Cross-Platform Support**: LinkedIn, Facebook, Instagram, Twitter
- **Persistent Sessions**: Login once, reuse sessions forever
- **HITL Workflow**: Human approval before posting
- **Retry Logic**: 3 attempts with exponential backoff
- **Error Recovery**: Screenshots on failure, detailed logging
- **Gold Tier Integration**: EventBus, AuditLogger, FolderManager, RetryQueue

## Architecture

```
/Approved → Executor → /Done (success)
                    → /Failed (after 3 retries)
```

## Installation

### Prerequisites

```bash
pip install playwright pyyaml
playwright install chromium
```

### Session Setup (One-Time)

Run the executor once per platform to log in and save sessions:

```bash
# This will open a browser for manual login
python3 Skills/social_media_executor/executor.py
```

Sessions are saved in `/Sessions/{platform}/` and persist across runs.

## Usage

### 1. Create Post File

Create a markdown file in `/Pending_Approval` with YAML frontmatter:

```markdown
---
platform: linkedin
type: post
content: "Excited to share my latest project!"
media: []
---

Optional additional content here (will be ignored if content is in frontmatter)
```

**Supported Platforms:**
- `linkedin` - Professional networking
- `facebook` - Social networking
- `instagram` - Photo/video sharing (requires media)
- `twitter` - Microblogging (280 char limit)

**Media Format:**
```yaml
media:
  - /path/to/image1.jpg
  - /path/to/image2.png
```

### 2. Approve Post

Move the file from `/Pending_Approval` to `/Approved`:

```bash
mv Pending_Approval/POST_linkedin_123.md Approved/
```

Or use FolderManager:
```python
folder_manager.move_to_approved("POST_linkedin_123.md")
```

### 3. Execute

The executor runs automatically via the orchestrator, or manually:

```bash
python3 Skills/social_media_executor/executor.py
```

### 4. Check Results

- **Success**: File moved to `/Done`
- **Failure**: File moved to `/Failed` with error details appended

## Configuration

Edit `config.json` to customize:

```json
{
  "platforms": {
    "linkedin": {
      "enabled": true,
      "selectors": { ... },
      "timeouts": { ... }
    }
  },
  "retry": {
    "max_attempts": 3,
    "initial_delay": 5000,
    "backoff_multiplier": 2
  },
  "browser": {
    "headless": false,
    "viewport": { "width": 1280, "height": 720 }
  }
}
```

## Platform-Specific Notes

### LinkedIn
- Handles "Start a post" button detection
- Supports text and media posts
- Uses keyboard.type() for reliability

### Facebook
- Multi-step flow (Next → Post/Share)
- Supports text and media posts
- Dynamic button detection

### Instagram
- **Requires media** (at least one image)
- Multi-step flow (Next → Next → Share)
- Caption is optional

### Twitter
- **280 character limit** enforced
- Supports text and media (up to 4 images)
- Real-time character counting

## Integration with Orchestrator

The executor integrates with Gold Tier infrastructure:

```python
from Skills.integration_orchestrator.core import FolderManager, EventBus, AuditLogger
from Skills.social_media_executor.executor import SocialMediaExecutorV2

executor = SocialMediaExecutorV2(
    base_dir=base_dir,
    event_bus=event_bus,
    audit_logger=audit_logger,
    folder_manager=folder_manager,
    logger=logger
)

results = await executor.process_approved_posts()
```

## Events Published

- `social.post.started` - Post execution started
- `social.post.completed` - Post successful
- `social.post.failed` - Post failed after retries

## Error Handling

On failure, the executor:
1. Takes screenshot → `/Logs/{platform}_error_{context}_{timestamp}.png`
2. Retries with exponential backoff (3 attempts)
3. Moves file to `/Failed` with error details
4. Publishes failure event
5. Logs to audit trail

## Troubleshooting

### "Not logged in" Error

Run the executor manually to log in:
```bash
python3 Skills/social_media_executor/executor.py
```

The browser will open in non-headless mode. Log in manually, then close the browser. The session will be saved.

### Selector Not Found

Platform UIs change frequently. Update selectors in `config.json`:

```json
{
  "platforms": {
    "linkedin": {
      "selectors": {
        "start_post_button": "[aria-label*='Start a post']",
        "editor": ".ql-editor"
      }
    }
  }
}
```

### Media Upload Failed

Ensure:
- File paths are absolute
- Files exist and are readable
- File formats are supported (JPG, PNG)

## Development

### Adding a New Platform

1. Create `platforms/newplatform.py`:
```python
from .base import BasePlatform

class NewPlatformPlatform(BasePlatform):
    def get_platform_url(self) -> str:
        return "https://newplatform.com"

    async def post(self, page, content, media):
        # Implementation
        pass
```

2. Register in `platforms/__init__.py`
3. Add configuration to `config.json`
4. Update `executor.py` platform mapping

## License

Part of AI Employee Vault - Gold Tier
