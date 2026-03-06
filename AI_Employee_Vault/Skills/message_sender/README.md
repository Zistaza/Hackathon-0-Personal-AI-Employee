# Message Sender v2

Unified message sending for Gmail and WhatsApp with HITL (Human-in-the-Loop) workflow.

## Features

- **Gmail**: Email sending via Gmail API with OAuth2
- **WhatsApp**: Messaging via WhatsApp Web automation
- **Persistent Sessions**: Login once, reuse forever
- **HITL Workflow**: Human approval before sending
- **Retry Logic**: 3 attempts with exponential backoff
- **Error Recovery**: Screenshots on failure, detailed logging
- **Gold Tier Integration**: EventBus, AuditLogger, FolderManager, RetryQueue

## Architecture

```
/Approved → Sender → /Done (success)
                  → /Failed (after 3 retries)
```

## Installation

### Prerequisites

```bash
# Gmail API
pip install google-api-python-client google-auth-oauthlib

# WhatsApp (Playwright)
pip install playwright pyyaml
playwright install chromium
```

### Gmail Setup (One-Time)

1. **Get Gmail API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download `credentials.json`
   - Place in project root: `AI_Employee_Vault/credentials.json`

2. **Authenticate:**
   ```bash
   python3 Skills/message_sender/sender.py
   ```
   This will open a browser for OAuth2 consent. Token saved to `/Sessions/gmail_token.json`.

### WhatsApp Setup (One-Time)

Run the sender once to scan QR code:

```bash
python3 Skills/message_sender/sender.py
```

Browser opens → Scan QR code with WhatsApp mobile → Session saved to `/Sessions/whatsapp/`.

## Usage

### 1. Create Message File

Create a markdown file in `/Pending_Approval` with YAML frontmatter:

**Gmail Example:**
```markdown
---
platform: gmail
type: message
to: "recipient@example.com"
subject: "Meeting Tomorrow"
content: "Hi, just confirming our meeting at 2pm tomorrow."
attachments: []
---

Optional additional content here (will be ignored if content is in frontmatter)
```

**WhatsApp Example:**
```markdown
---
platform: whatsapp
type: message
to: "John Doe"
subject: ""
content: "Hey John, can we reschedule our call to 3pm?"
---
```

**With Attachments (Gmail only):**
```yaml
---
platform: gmail
type: message
to: "client@company.com"
subject: "Project Proposal"
content: "Please find attached the project proposal."
attachments:
  - /path/to/proposal.pdf
  - /path/to/budget.xlsx
---
```

### 2. Approve Message

Move the file from `/Pending_Approval` to `/Approved`:

```bash
mv Pending_Approval/MESSAGE_gmail_123.md Approved/
```

Or use FolderManager:
```python
folder_manager.move_to_approved("MESSAGE_gmail_123.md")
```

### 3. Execute

The sender runs automatically via the orchestrator, or manually:

```bash
python3 Skills/message_sender/sender.py
```

### 4. Check Results

- **Success**: File moved to `/Done`
- **Failure**: File moved to `/Failed` with error details appended

## Configuration

Edit `config.json` to customize:

```json
{
  "platforms": {
    "gmail": {
      "enabled": true,
      "scopes": ["gmail.send", "gmail.readonly"],
      "max_attachments": 25
    },
    "whatsapp": {
      "enabled": true,
      "selectors": { ... },
      "timeouts": { ... }
    }
  },
  "retry": {
    "max_attempts": 3,
    "initial_delay": 5000,
    "backoff_multiplier": 2
  }
}
```

## Platform-Specific Notes

### Gmail
- Uses Gmail API (official, reliable)
- OAuth2 authentication required
- Supports attachments (up to 25MB per file, 25 files max)
- Supports HTML emails (use HTML in content)
- Rate limits: 500 emails/day (free), 2000/day (workspace)

### WhatsApp
- Uses WhatsApp Web automation (unofficial)
- QR code authentication required
- Contact name must match exactly as in WhatsApp
- No attachment support yet
- Subject field ignored (WhatsApp doesn't have subjects)
- Rate limits: Avoid sending too many messages quickly

## Integration with Orchestrator

The sender integrates with Gold Tier infrastructure:

```python
from Skills.integration_orchestrator.core import FolderManager, EventBus, AuditLogger
from Skills.message_sender.sender import MessageSenderV2

sender = MessageSenderV2(
    base_dir=base_dir,
    event_bus=event_bus,
    audit_logger=audit_logger,
    folder_manager=folder_manager,
    logger=logger
)

results = await sender.process_approved_messages()
```

## Events Published

- `message.send.started` - Message sending started
- `message.send.completed` - Message sent successfully
- `message.send.failed` - Message failed after retries

## Error Handling

On failure, the sender:
1. Takes screenshot (WhatsApp only) → `/Logs/whatsapp_error_{context}_{timestamp}.png`
2. Retries with exponential backoff (3 attempts)
3. Moves file to `/Failed` with error details
4. Publishes failure event
5. Logs to audit trail

## Troubleshooting

### Gmail: "Credentials not found"

Ensure `credentials.json` is in the project root:
```bash
ls -la AI_Employee_Vault/credentials.json
```

If missing, download from Google Cloud Console.

### Gmail: "Token expired"

Delete the token and re-authenticate:
```bash
rm Sessions/gmail_token.json
python3 Skills/message_sender/sender.py
```

### WhatsApp: "Not logged in"

Run the sender manually to scan QR code:
```bash
python3 Skills/message_sender/sender.py
```

Browser opens in non-headless mode. Scan QR code with your phone.

### WhatsApp: "Contact not found"

Ensure the contact name matches exactly as it appears in WhatsApp:
- Case-sensitive
- Include spaces and special characters
- Use the saved contact name, not phone number

### Selector Not Found

WhatsApp Web UI changes frequently. Update selectors in `config.json`:

```json
{
  "platforms": {
    "whatsapp": {
      "selectors": {
        "search_box": "[data-testid='chat-list-search']",
        "message_box": "[data-testid='conversation-compose-box-input']"
      }
    }
  }
}
```

## File Naming Convention

- **Posts**: `POST_{platform}_{timestamp}.md`
- **Messages**: `MESSAGE_{platform}_{timestamp}.md`

This helps the system distinguish between social media posts and direct messages.

## Security Notes

- **Gmail tokens** contain OAuth2 credentials - keep secure
- **WhatsApp sessions** contain authentication data - keep secure
- Never commit `credentials.json` or token files to git
- Add to `.gitignore`:
  ```
  credentials.json
  Sessions/gmail_token.json
  Sessions/whatsapp/
  ```

## License

Part of AI Employee Vault - Gold Tier
