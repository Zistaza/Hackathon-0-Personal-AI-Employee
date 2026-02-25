---
title: Gmail Watcher Skill
created_at: 2026-02-22T03:14:00Z
version: 1.0
tier: Silver
skill_type: external_integration
---

# Gmail Watcher Skill

## Purpose

Automatically monitor Gmail for unread important emails, create structured action items in `/Needs_Action`, prevent duplicate processing, and maintain comprehensive logs following Silver Tier architecture.

## Features

- ✅ Gmail API integration
- ✅ Monitors unread important emails only
- ✅ Creates markdown files with metadata headers
- ✅ Duplicate prevention using processed_ids.json
- ✅ Per-action logging to /Logs
- ✅ Silver Tier architecture compliance
- ✅ OAuth 2.0 authentication
- ✅ Error handling and recovery

---

## Prerequisites

### 1. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json`
6. Place in vault root: `/AI_Employee_Vault/credentials.json`

### 2. Node.js Dependencies

```bash
cd /home/emizee/AI_Employee_Vault/AI_Employee_Vault
npm install googleapis
```

### 3. First-Time Authorization

```bash
node Skills/gmail_watcher_skill/gmail_watcher.js
```

Follow the authorization URL, grant permissions, and the token will be saved automatically.

---

## File Structure

```
Skills/gmail_watcher_skill/
├── gmail_watcher.js          # Main skill script
├── processed_ids.json         # Tracks processed email IDs
├── token.json                 # OAuth token (auto-generated)
└── SKILL.md                   # This documentation
```

---

## Usage

### Manual Execution

```bash
cd /home/emizee/AI_Employee_Vault/AI_Employee_Vault
node Skills/gmail_watcher_skill/gmail_watcher.js
```

### Scheduled Execution (Cron)

```bash
# Check every 15 minutes
*/15 * * * * cd /home/emizee/AI_Employee_Vault/AI_Employee_Vault && node Skills/gmail_watcher_skill/gmail_watcher.js >> Skills/gmail_watcher_skill/cron.log 2>&1
```

### Integration with AI Employee

Tell your AI Employee:
```
Run the gmail_watcher_skill to check for new important emails
```

---

## Output Format

### Created File: `/Needs_Action/email_<id>.md`

```markdown
---
type: email
from: sender@example.com
subject: Important Project Update
received: 2026-02-22T10:30:00Z
status: pending
email_id: 18d4f2a3b5c6e7f8
created: 2026-02-22T10:35:00Z
---

# Email: Important Project Update

## From
sender@example.com

## Received
2026-02-22T10:30:00Z

## Content

[Email body content here...]

---

*This email requires action. Review and create a plan in the process_needs_action workflow.*
```

### Log Entry: `/Logs/YYYY-MM-DD.json`

```json
{
  "timestamp": "2026-02-22T10:35:00Z",
  "action_type": "gmail_watcher",
  "email_id": "18d4f2a3b5c6e7f8",
  "subject": "Important Project Update",
  "from": "sender@example.com",
  "file_created": "email_18d4f2a3b5c6e7f8.md",
  "result": "success"
}
```

### Processed IDs: `processed_ids.json`

```json
{
  "processed_ids": [
    "18d4f2a3b5c6e7f8",
    "19e5g3b4c6d7f9a0"
  ],
  "last_check": "2026-02-22T10:35:00Z"
}
```

---

## Workflow Integration

```
┌─────────────────┐
│  Gmail Inbox    │
│ (Important +    │
│   Unread)       │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ gmail_watcher.js    │ (This Skill)
│ - Fetch emails      │
│ - Check duplicates  │
│ - Create .md files  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Needs_Action/      │
│  email_*.md         │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ process_needs_action│ (Existing Skill)
│ - Analyze email     │
│ - Create plan       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Pending_Approval/   │
│ PLAN_email_*.md     │
└─────────────────────┘
```

---

## Safety Features

### Duplicate Prevention
- Tracks all processed email IDs in `processed_ids.json`
- Skips emails already processed
- Prevents duplicate action items
- Maintains processing history

### Error Handling
- Graceful API failures
- Continues on individual email errors
- Logs all errors for review
- Preserves processed IDs on failure

### Logging
- Per-action log entries
- Uses existing `append_log.py` utility
- Atomic log writes
- Corruption detection and recovery

### Data Safety
- Read-only Gmail access
- No email deletion or modification
- All files created, never deleted
- Complete audit trail

---

## Configuration

Edit `gmail_watcher.js` to customize:

```javascript
const CONFIG = {
  CREDENTIALS_PATH: path.join(__dirname, '../../credentials.json'),
  TOKEN_PATH: path.join(__dirname, 'token.json'),
  PROCESSED_IDS_PATH: path.join(__dirname, 'processed_ids.json'),
  NEEDS_ACTION_DIR: path.join(__dirname, '../../Needs_Action'),
  LOGS_DIR: path.join(__dirname, '../../Logs'),
  APPEND_LOG_SCRIPT: path.join(__dirname, '../process_needs_action/append_log.py'),
  SCOPES: ['https://www.googleapis.com/auth/gmail.readonly']
};
```

### Gmail Query Customization

Change the query in `fetchUnreadImportantEmails()`:

```javascript
// Current: unread + important
q: 'is:unread is:important'

// Examples:
q: 'is:unread label:urgent'           // Specific label
q: 'is:unread from:boss@company.com'  // Specific sender
q: 'is:unread subject:URGENT'         // Subject keyword
```

---

## Troubleshooting

### "Authorize this app by visiting this url"
- First-time setup required
- Visit the URL, grant permissions
- Run script again after authorization

### "Error: invalid_grant"
- Token expired or revoked
- Delete `token.json`
- Re-authorize by running script

### "No emails found"
- Check Gmail for unread important emails
- Verify Gmail query matches your needs
- Check API quota limits

### "Logging failed"
- Ensure `append_log.py` exists
- Verify Python 3 is installed
- Check `/Logs` directory permissions

### "Cannot find module 'googleapis'"
- Run: `npm install googleapis`
- Verify `node_modules` directory exists

---

## Maintenance

### Clear Processed IDs (Reset)

```bash
echo '{"processed_ids":[],"last_check":null}' > Skills/gmail_watcher_skill/processed_ids.json
```

### View Processed Count

```bash
node -e "console.log(require('./Skills/gmail_watcher_skill/processed_ids.json').processed_ids.length)"
```

### Archive Old Processed IDs

```bash
# Backup current processed IDs
cp Skills/gmail_watcher_skill/processed_ids.json Skills/gmail_watcher_skill/processed_ids.$(date +%Y%m%d).backup

# Reset to empty
echo '{"processed_ids":[],"last_check":null}' > Skills/gmail_watcher_skill/processed_ids.json
```

---

## Performance

- Fetches max 10 emails per run (configurable)
- Processes emails sequentially
- Minimal API calls (1 list + N get)
- Efficient duplicate checking (O(n) lookup)
- Lightweight file operations

---

## Security

- OAuth 2.0 authentication
- Read-only Gmail access
- Credentials stored locally
- No email content sent externally
- Token refresh handled automatically

---

## Version History

**v1.0** (2026-02-22)
- Initial implementation
- Gmail API integration
- Duplicate prevention
- Per-action logging
- Silver Tier compliance
