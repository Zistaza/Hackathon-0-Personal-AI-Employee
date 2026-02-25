# AI Employee Watchers

Production-ready Python watchers for monitoring Gmail, WhatsApp, and LinkedIn.

## Architecture

All watchers inherit from `BaseWatcher` abstract class, providing:
- Continuous monitoring with configurable intervals
- Duplicate detection and tracking
- Keyword filtering
- Automatic markdown file creation in `/Needs_Action`
- Comprehensive logging
- Graceful shutdown handling

## Watchers

### Gmail Watcher
- Monitors Gmail inbox for unread emails
- Uses Gmail API for reliable access
- Requires OAuth2 authentication
- Default check interval: 5 minutes

### WhatsApp Watcher
- Monitors WhatsApp Web for unread messages
- Uses Playwright browser automation
- Maintains persistent session
- Default check interval: 5 minutes

### LinkedIn Watcher
- Monitors LinkedIn messages and notifications
- Uses Playwright browser automation
- Maintains persistent session
- Default check interval: 10 minutes (rate limiting)

## Installation

### 1. Install Python Dependencies

```bash
cd Automation/watchers
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Setup Gmail API (Gmail Watcher Only)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json`
6. Place in project root: `AI_Employee_Vault/credentials.json`

### 4. First Run Setup

**Gmail Watcher:**
```bash
python3 gmail_watcher.py
# Browser will open for OAuth consent
# Grant permissions
# Token saved to gmail_token.pickle
```

**WhatsApp Watcher:**
```bash
python3 whatsapp_watcher.py
# Browser opens with WhatsApp Web
# Scan QR code with phone
# Session saved to whatsapp_session/
```

**LinkedIn Watcher:**
```bash
python3 linkedin_watcher.py
# Browser opens with LinkedIn
# Login manually
# Session saved to linkedin_session/
```

## Usage

### Run Individual Watcher

```bash
# Gmail
python3 gmail_watcher.py

# WhatsApp
python3 whatsapp_watcher.py

# LinkedIn
python3 linkedin_watcher.py
```

### Run All Watchers

```bash
python3 run_all_watchers.py
```

This starts all watchers in separate processes.

### Run as Background Service

```bash
# Using nohup
nohup python3 run_all_watchers.py > watcher.log 2>&1 &

# Using screen
screen -S watchers
python3 run_all_watchers.py
# Press Ctrl+A, then D to detach

# Using systemd (see systemd section below)
```

## Configuration

### Keywords

Edit keywords in each watcher file or pass as parameter:

```python
watcher = GmailWatcher(
    keywords=["invoice", "urgent", "payment", "proposal", "contract"]
)
```

### Check Intervals

```python
watcher = GmailWatcher(
    check_interval=300  # 5 minutes in seconds
)
```

### Headless Mode (WhatsApp/LinkedIn)

```python
watcher = WhatsAppWatcher(
    headless=True  # Run without visible browser
)
```

## Output Format

All watchers create markdown files in `/Needs_Action`:

```markdown
---
type: gmail|whatsapp|linkedin_message|linkedin_notification
sender: John Doe
timestamp: 2026-02-23T10:30:00Z
status: pending
[additional metadata]
---

[Message content]
```

## Logging

Logs are written to `/Logs/`:
- `gmail_watcher.log`
- `whatsapp_watcher.log`
- `linkedin_watcher.log`

Log format:
```
[2026-02-23 10:30:00] [gmail_watcher] [INFO] Starting check cycle...
[2026-02-23 10:30:05] [gmail_watcher] [INFO] Found 3 event(s)
[2026-02-23 10:30:06] [gmail_watcher] [INFO] Processed 2 new event(s)
```

## Duplicate Prevention

Each watcher maintains a tracking file:
- `gmail_processed.json`
- `whatsapp_processed.json`
- `linkedin_processed.json`

These files store IDs of processed items to prevent duplicates.

## Systemd Service (Linux)

Create `/etc/systemd/system/ai-employee-watchers.service`:

```ini
[Unit]
Description=AI Employee Watchers
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/AI_Employee_Vault/Automation/watchers
ExecStart=/usr/bin/python3 run_all_watchers.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-employee-watchers
sudo systemctl start ai-employee-watchers
sudo systemctl status ai-employee-watchers
```

## Troubleshooting

### Gmail Watcher

**Error: credentials.json not found**
- Place credentials.json in project root
- Path: `AI_Employee_Vault/credentials.json`

**Error: Token expired**
- Delete `gmail_token.pickle`
- Run watcher again to re-authenticate

### WhatsApp Watcher

**QR code timeout**
- Increase timeout in code
- Ensure phone has internet connection
- Try again

**Session expired**
- Delete `whatsapp_session/` directory
- Run watcher again to re-login

**Selectors not working**
- WhatsApp Web UI may have changed
- Update selectors in code

### LinkedIn Watcher

**Login required every time**
- Check `linkedin_session/` permissions
- Ensure directory is writable
- LinkedIn may require periodic re-authentication

**Rate limiting**
- Increase check_interval (default: 600 seconds)
- LinkedIn monitors automated access

### General Issues

**High CPU usage**
- Increase check intervals
- Use headless mode for browser watchers
- Check for infinite loops in logs

**Memory leaks**
- Restart watchers periodically
- Monitor with `top` or `htop`
- Check logs for errors

**No events detected**
- Verify keywords are correct
- Check logs for errors
- Ensure services are accessible
- Test authentication

## File Structure

```
Automation/watchers/
├── base_watcher.py           # Abstract base class
├── gmail_watcher.py          # Gmail implementation
├── whatsapp_watcher.py       # WhatsApp implementation
├── linkedin_watcher.py       # LinkedIn implementation
├── run_all_watchers.py       # Manager for all watchers
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── setup.sh                  # Setup script
├── gmail_processed.json      # Gmail tracking (auto-generated)
├── whatsapp_processed.json   # WhatsApp tracking (auto-generated)
├── linkedin_processed.json   # LinkedIn tracking (auto-generated)
├── gmail_token.pickle        # Gmail auth token (auto-generated)
├── whatsapp_session/         # WhatsApp session (auto-generated)
└── linkedin_session/         # LinkedIn session (auto-generated)
```

## Integration with AI Employee

Watchers create files in `/Needs_Action`, which are automatically processed by:

1. **process_needs_action** skill
   - Reads files from `/Needs_Action`
   - Analyzes content
   - Creates comprehensive plans with risk analysis
   - Moves to `/Pending_Approval`

2. **Human Review**
   - Reviews plans in `/Pending_Approval`
   - Approves or rejects

3. **Execution**
   - Approved plans are executed
   - Results documented

## Performance

### Resource Usage (Typical)

**Gmail Watcher:**
- CPU: <1% (idle), 5-10% (checking)
- Memory: ~50MB
- Network: Minimal (API calls only)

**WhatsApp Watcher:**
- CPU: 2-5% (idle), 10-20% (checking)
- Memory: ~200MB (browser)
- Network: Moderate (WebSocket connection)

**LinkedIn Watcher:**
- CPU: 2-5% (idle), 10-20% (checking)
- Memory: ~200MB (browser)
- Network: Moderate (page loads)

### Optimization Tips

1. **Increase check intervals** for less frequent monitoring
2. **Use headless mode** for browser watchers to reduce CPU
3. **Limit max_results** to process fewer items per check
4. **Run on dedicated server** for 24/7 operation
5. **Use systemd** for automatic restart on failure

## Security

### Best Practices

1. **Never commit session files** to version control
2. **Protect credentials.json** with appropriate permissions
3. **Use environment variables** for sensitive config
4. **Rotate tokens** periodically
5. **Monitor logs** for suspicious activity
6. **Use HTTPS** for all API calls
7. **Limit API scopes** to minimum required

### File Permissions

```bash
chmod 600 credentials.json
chmod 600 gmail_token.pickle
chmod 700 whatsapp_session/
chmod 700 linkedin_session/
chmod 600 *_processed.json
```

## Development

### Adding a New Watcher

1. Create new file: `my_watcher.py`
2. Inherit from `BaseWatcher`
3. Implement required methods:
   - `initialize()` - Setup connections
   - `check_for_events()` - Fetch new events
   - `cleanup()` - Cleanup resources
4. Add to `run_all_watchers.py`

Example:
```python
from base_watcher import BaseWatcher

class MyWatcher(BaseWatcher):
    def initialize(self) -> bool:
        # Setup code
        return True

    def check_for_events(self) -> List[Dict]:
        # Fetch events
        return events

    def cleanup(self):
        # Cleanup code
        pass
```

### Testing

```bash
# Test individual watcher
python3 gmail_watcher.py

# Test with custom config
python3 -c "
from gmail_watcher import GmailWatcher
w = GmailWatcher(check_interval=60, keywords=['test'])
w.run()
"
```

## Support

For issues or questions:
1. Check logs in `/Logs/`
2. Review this README
3. Check watcher-specific documentation
4. Verify authentication and permissions

## Version History

**v1.0** (2026-02-23)
- Initial production release
- Gmail, WhatsApp, LinkedIn watchers
- Base watcher architecture
- Continuous monitoring
- Duplicate prevention
- Comprehensive logging
