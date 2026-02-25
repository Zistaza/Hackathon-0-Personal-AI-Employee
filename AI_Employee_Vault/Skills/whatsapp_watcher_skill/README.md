# WhatsApp Watcher Skill

Monitors WhatsApp Web for unread messages containing specific keywords and automatically creates action items.

## Features

- **Persistent Session**: Uses Playwright persistent context to maintain WhatsApp login
- **Keyword Detection**: Scans messages for: invoice, urgent, payment, proposal
- **Auto Action Files**: Creates markdown files in `/Needs_Action` for matched messages
- **Duplicate Prevention**: Tracks processed messages in `processed_ids.json`
- **Comprehensive Logging**: All activity logged to `/Logs/whatsapp_watcher.log`
- **Retry Handling**: Automatic retry on browser failures (max 3 attempts)

## Installation

```bash
cd Skills/whatsapp_watcher_skill
npm install
```

## First Run Setup

1. Run the skill for the first time:
```bash
node index.js
```

2. A browser window will open with WhatsApp Web
3. Scan the QR code with your phone to login
4. The session will be saved in `whatsapp_session/` directory
5. Future runs will use the saved session automatically

## Usage

Run manually:
```bash
node index.js
```

Or schedule with cron (every 5 minutes):
```bash
*/5 * * * * cd /path/to/Skills/whatsapp_watcher_skill && node index.js
```

## Configuration

Edit keywords in `index.js` (line 331):
```javascript
keywords: ['invoice', 'urgent', 'payment', 'proposal']
```

## Output Format

When a keyword match is found, creates: `/Needs_Action/whatsapp_<timestamp>.md`

```markdown
---
type: whatsapp
sender: John Doe
timestamp: 2026-02-23T10:30:00.000Z
status: pending
---

Please send the invoice for last month's services.
```

## File Structure

```
whatsapp_watcher_skill/
├── index.js              # Main implementation
├── package.json          # Dependencies
├── skill.json           # Skill configuration
├── processed_ids.json   # Tracking file (auto-generated)
├── whatsapp_session/    # Browser session data (auto-generated)
└── README.md           # This file
```

## Logs

All activity is logged to: `/Logs/whatsapp_watcher.log`

Example log entries:
```
[2026-02-23T10:30:00.000Z] Starting WhatsApp scan...
[2026-02-23T10:30:05.000Z] Found 3 unread chat(s)
[2026-02-23T10:30:08.000Z] Keyword match found in message from John Doe
[2026-02-23T10:30:08.000Z] Created action file: whatsapp_1708684208000.md
```

## Troubleshooting

**QR Code appears every time:**
- The session data may not be saving properly
- Check that `whatsapp_session/` directory has write permissions

**No unread chats detected:**
- WhatsApp Web selectors may have changed
- Check browser console for errors
- Verify you have unread messages in WhatsApp

**Browser fails to launch:**
- Ensure Playwright is installed: `npm install`
- Install browser binaries: `npx playwright install chromium`

## Security Notes

- Session data contains authentication tokens
- Never commit `whatsapp_session/` directory
- Keep `processed_ids.json` private (contains chat metadata)
- Review `.gitignore` to ensure sensitive files are excluded
