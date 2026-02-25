# Gmail Watcher Skill - Quick Start

Monitor Gmail for unread important emails and automatically create action items.

## Setup (One-Time)

1. **Install dependencies:**
   ```bash
   npm install googleapis
   ```

2. **Place Gmail credentials:**
   - Download OAuth credentials from Google Cloud Console
   - Save as `/AI_Employee_Vault/credentials.json`

3. **First run (authorization):**
   ```bash
   node Skills/gmail_watcher_skill/gmail_watcher.js
   ```
   - Visit the authorization URL
   - Grant permissions
   - Token saved automatically

## Usage

```bash
# Run manually
node Skills/gmail_watcher_skill/gmail_watcher.js

# Or via AI Employee
"Run gmail_watcher_skill to check for new emails"
```

## What It Does

1. ✅ Fetches unread important emails from Gmail
2. ✅ Creates `.md` files in `/Needs_Action` with metadata
3. ✅ Prevents duplicates using `processed_ids.json`
4. ✅ Logs all actions to `/Logs/YYYY-MM-DD.json`
5. ✅ Integrates with existing `process_needs_action` workflow

## Output Example

**File:** `/Needs_Action/email_abc123.md`

```markdown
---
type: email
from: sender@example.com
subject: Important Update
received: 2026-02-22T10:30:00Z
status: pending
---

# Email: Important Update

## From
sender@example.com

## Content
[Email body...]
```

## Troubleshooting

- **"Authorize this app"** → First-time setup, follow the URL
- **"invalid_grant"** → Delete `token.json` and re-authorize
- **"No emails found"** → Check Gmail for unread important emails

See `SKILL.md` for complete documentation.
