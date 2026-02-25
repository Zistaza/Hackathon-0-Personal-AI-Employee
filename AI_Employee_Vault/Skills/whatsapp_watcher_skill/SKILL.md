---
title: WhatsApp Watcher Skill
created_at: 2026-02-23T02:30:00Z
version: 1.0
tier: Silver
skill_type: automated_monitoring
---

# WhatsApp Watcher Skill

## Purpose

Monitors WhatsApp Web for unread messages containing specific keywords and automatically creates action items in the `/Needs_Action` folder.

## Skill Overview

This skill uses Playwright browser automation to maintain a persistent WhatsApp Web session, scan for unread messages, filter by keywords, and create structured markdown files for matched messages.

---

## Features

- **Persistent Session**: Uses Playwright persistent context to maintain WhatsApp login
- **Keyword Detection**: Scans messages for: invoice, urgent, payment, proposal
- **Auto Action Files**: Creates markdown files in `/Needs_Action` for matched messages
- **Duplicate Prevention**: Tracks processed messages in `processed_ids.json`
- **Comprehensive Logging**: All activity logged to `/Logs/whatsapp_watcher.log`
- **Retry Handling**: Automatic retry on browser failures (max 3 attempts)

---

## Configuration

Edit `config.json` to customize:

```json
{
  "keywords": ["invoice", "urgent", "payment", "proposal"],
  "paths": {
    "needsActionDir": "../../Needs_Action",
    "logsDir": "../../Logs",
    "processedIdsFile": "./processed_ids.json",
    "userDataDir": "./whatsapp_session"
  },
  "retry": {
    "maxRetries": 3,
    "retryDelay": 5000
  }
}
```

---

## Execution Steps

### Step 1: Initialize Browser Session

**Action**: Launch Chromium with persistent context

**Details**:
- Uses saved session from `whatsapp_session/` directory
- Opens WhatsApp Web in non-headless mode
- Maintains login across runs

**First Run**:
- QR code will appear
- Scan with phone to login
- Session saved automatically

### Step 2: Navigate to WhatsApp Web

**Action**: Load https://web.whatsapp.com

**Validation**:
- Wait for either QR code or chat list
- If QR code: wait for user to scan (up to 2 minutes)
- If chat list: already logged in

### Step 3: Scan for Unread Chats

**Action**: Find all chats with unread message indicators

**Selectors Used**:
- `[data-testid="cell-frame-container"]` - Chat containers
- `[data-testid="icon-unread-count"]` - Unread badge
- `[data-testid="cell-frame-title"]` - Chat name

**Output**: Array of unread chat objects with name and ID

### Step 4: Process Each Unread Chat

**Action**: Click chat and extract messages

**Sub-steps**:
1. Click on chat element
2. Wait for messages to load (2 seconds)
3. Extract last 20 messages
4. Filter for incoming messages only
5. Check each message for keywords

### Step 5: Extract Message Content

**Action**: Parse message text and metadata

**Selectors Used**:
- `[data-testid="msg-container"]` - Message containers
- `[data-testid="tail-in"]` - Incoming message indicator
- `[data-testid="conversation-text-content"]` - Message text
- `[data-testid="msg-meta"]` - Message metadata

### Step 6: Keyword Matching

**Action**: Check if message contains any configured keywords

**Logic**:
- Convert message to lowercase
- Check if any keyword is substring of message
- Case-insensitive matching

**Keywords** (default):
- invoice
- urgent
- payment
- proposal

### Step 7: Create Action File

**Action**: Generate markdown file in `/Needs_Action`

**Filename**: `whatsapp_<timestamp>.md`

**Format**:
```markdown
---
type: whatsapp
sender: <chat name>
timestamp: <ISO 8601 timestamp>
status: pending
---

<message content>
```

### Step 8: Track Processed Messages

**Action**: Add message ID to `processed_ids.json`

**Purpose**: Prevent duplicate processing

**Message ID Format**: `{chat_id}_{timestamp}_{content_preview}`

### Step 9: Log Activity

**Action**: Append to `/Logs/whatsapp_watcher.log`

**Log Entries**:
- Scan started
- Unread chats found
- Keyword matches
- Action files created
- Errors encountered

### Step 10: Close Browser

**Action**: Close browser context

**Note**: Session data is preserved in `whatsapp_session/`

---

## Safety Rules

### Session Security
- Never commit `whatsapp_session/` directory
- Contains authentication tokens
- Add to `.gitignore`

### Message Privacy
- Only processes unread messages
- Does not modify or delete messages
- Does not send messages

### Error Handling
- Retry on browser failures (3 attempts)
- Continue processing on individual chat errors
- Log all errors for review

---

## Expected Outcomes

After successful execution:

1. All unread messages scanned
2. Keyword-matching messages have action files in `/Needs_Action`
3. Message IDs tracked in `processed_ids.json`
4. Activity logged to `/Logs/whatsapp_watcher.log`
5. Browser session maintained for next run
6. No messages modified or deleted in WhatsApp

---

## Error Scenarios

### Scenario 1: QR Code Timeout
**Symptom**: User doesn't scan QR code within 2 minutes
**Action**: Exit with error, retry on next run

### Scenario 2: WhatsApp Web Changes
**Symptom**: Selectors no longer match elements
**Action**: Log error, update selectors in code

### Scenario 3: Network Issues
**Symptom**: Page fails to load
**Action**: Retry up to 3 times with 5-second delay

### Scenario 4: File Write Failure
**Symptom**: Cannot create action file
**Action**: Log error, continue with next message

---

## Usage

### Manual Invocation
```bash
cd Skills/whatsapp_watcher_skill
./run.sh
```

### Automated Invocation
Add to crontab:
```bash
*/5 * * * * cd /path/to/Skills/whatsapp_watcher_skill && ./run.sh
```

### First Run Setup
```bash
cd Skills/whatsapp_watcher_skill
./setup.sh
node index.js
# Scan QR code when prompted
```

---

## Performance Considerations

- Processes only last 20 messages per chat
- Scans only unread chats
- Uses efficient selectors
- Maintains persistent session (no re-login)
- Configurable scan frequency

---

## Maintenance

### Regular Checks
- Verify session is still valid
- Check log file for errors
- Confirm action files are being created
- Review processed_ids.json size

### Cleanup
- Archive old logs monthly
- Clear processed_ids.json if too large (keep last 1000)
- Update WhatsApp Web selectors if UI changes

---

## Integration

### With process_needs_action Skill
- WhatsApp Watcher creates files in `/Needs_Action`
- process_needs_action picks them up automatically
- Creates plans with risk analysis
- Moves to `/Pending_Approval` for review

### Workflow
1. WhatsApp message received
2. WhatsApp Watcher detects keyword
3. Action file created in `/Needs_Action`
4. process_needs_action generates plan
5. Plan moved to `/Pending_Approval`
6. Human reviews and approves
7. Action executed

---

## Version History

**v1.0** (2026-02-23)
- Initial implementation
- Playwright browser automation
- Keyword filtering
- Duplicate prevention
- Comprehensive logging
- Retry handling
