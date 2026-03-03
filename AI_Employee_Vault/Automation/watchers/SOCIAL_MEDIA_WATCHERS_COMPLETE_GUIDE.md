# Social Media Watchers - Complete Setup Guide

## Overview

You now have **complete social media monitoring** using browser automation to access your real accounts. No API keys needed!

## Available Watchers

| Platform | Monitors | Keywords | Interval |
|----------|----------|----------|----------|
| **Gmail** | Emails | invoice, urgent, payment, proposal | 5 min |
| **WhatsApp** | Messages | invoice, urgent, payment, proposal | 5 min |
| **LinkedIn** | Messages, Notifications | job, opportunity, interview, proposal, project | 10 min |
| **Facebook** | Notifications, Messages | urgent, important, invoice, payment, proposal | 10 min |
| **Instagram** | Notifications, DMs | urgent, important, collab, partnership, business | 10 min |
| **Twitter/X** | Notifications, DMs | urgent, important, mention, dm, message | 10 min |

## Quick Start - 3 Steps

### Step 1: Authenticate All Platforms

Run these commands in your terminal (one at a time):

```bash
cd Automation/watchers

# Social media platforms (browser will open for each)
python3 authenticate_facebook.py
python3 authenticate_instagram.py
python3 authenticate_twitter.py
```

**Note**: WhatsApp and LinkedIn authentication is done through their respective watchers on first run.

### Step 2: Test Individual Watchers

Test each watcher to make sure it works:

```bash
# Test Facebook
python3 facebook_watcher.py

# Test Instagram
python3 instagram_watcher.py

# Test Twitter/X
python3 twitter_watcher.py
```

Press `Ctrl+C` to stop each test.

### Step 3: Run All Watchers Together

Start monitoring all platforms simultaneously:

```bash
python3 run_all_watchers.py
```

This runs all 6 watchers in separate processes. They'll monitor continuously and create action files in `Needs_Action/` when they find matching content.

## How It Works

### Browser Automation Approach

Instead of using expensive APIs (Twitter API costs $100+/month), we use **browser automation**:

1. **Playwright** controls a real Chrome browser
2. You log in once, session is saved
3. Watchers run in headless mode (background)
4. They scrape notifications/messages from the web interface
5. Matching items create markdown files in `Needs_Action/`

### Session Management

Each platform stores its session separately:
- `facebook_session/` - Facebook login
- `instagram_session/` - Instagram login
- `twitter_session/` - Twitter/X login
- `whatsapp_session/` - WhatsApp Web login
- `linkedin_session/` - LinkedIn login

**Security**: These directories are in `.gitignore` and never committed.

### Keyword Filtering

Only items containing your keywords trigger action files. Customize keywords in `run_all_watchers.py`:

```python
keywords=["your", "custom", "keywords"]
```

### Duplicate Prevention

Each watcher tracks processed items in `*_processed.json` files to avoid creating duplicate action files.

## File Structure

```
Automation/watchers/
├── authenticate_facebook.py      # Facebook login script
├── authenticate_instagram.py     # Instagram login script
├── authenticate_twitter.py       # Twitter/X login script
├── base_watcher.py              # Base class for all watchers
├── facebook_watcher.py          # Facebook monitoring
├── instagram_watcher.py         # Instagram monitoring
├── twitter_watcher.py           # Twitter/X monitoring
├── whatsapp_watcher.py          # WhatsApp monitoring
├── linkedin_watcher.py          # LinkedIn monitoring
├── gmail_watcher.py             # Gmail monitoring
├── run_all_watchers.py          # Run all watchers together
├── FACEBOOK_SETUP_GUIDE.md      # Detailed Facebook guide
├── INSTAGRAM_SETUP_GUIDE.md     # Detailed Instagram guide
├── TWITTER_SETUP_GUIDE.md       # Detailed Twitter/X guide
└── *_session/                   # Session directories (not in git)
```

## Output Files

When a watcher finds matching content, it creates a markdown file:

**Location**: `Needs_Action/[platform]_[timestamp].md`

**Example** (`Needs_Action/facebook_1234567890.md`):
```markdown
---
type: facebook_notification
timestamp: 2026-03-03T10:30:00Z
status: pending
---

John Doe mentioned you in a comment: "Can you send me the invoice?"
```

## Configuration

### Change Check Intervals

Edit `run_all_watchers.py`:

```python
check_interval=600,  # 600 seconds = 10 minutes
```

**Recommendations**:
- Gmail/WhatsApp: 300 seconds (5 min)
- LinkedIn: 600 seconds (10 min)
- Facebook: 600 seconds (10 min)
- Instagram: 900 seconds (15 min) - more aggressive detection
- Twitter/X: 900 seconds (15 min) - more aggressive detection

### Customize Keywords Per Platform

Edit `run_all_watchers.py` to set different keywords for each platform:

```python
# Professional platforms
'LinkedIn': {
    'keywords': ["job", "opportunity", "interview", "proposal"]
}

# Business platforms
'Facebook': {
    'keywords': ["invoice", "payment", "urgent", "client"]
}

# Creative platforms
'Instagram': {
    'keywords': ["collab", "partnership", "sponsor", "business"]
}
```

### Enable/Disable Specific Watchers

Comment out watchers you don't want to run in `run_all_watchers.py`:

```python
# Don't start Instagram watcher
# self.start_watcher(InstagramWatcher, "Instagram", ...)
```

### Headless vs Visible Mode

For debugging, run watchers with visible browser:

Edit `run_all_watchers.py`:
```python
headless=False,  # Shows browser window
```

## Monitoring & Logs

### Check Watcher Status

Logs are saved in `Logs/` directory:
- `Logs/facebook_watcher.log`
- `Logs/instagram_watcher.log`
- `Logs/twitter_watcher.log`
- etc.

### View Real-Time Logs

```bash
tail -f Logs/facebook_watcher.log
tail -f Logs/instagram_watcher.log
tail -f Logs/twitter_watcher.log
```

### Check Processed Items

Each watcher tracks what it has processed:
- `facebook_processed.json`
- `instagram_processed.json`
- `twitter_processed.json`

## Troubleshooting

### Session Expired

If a watcher reports login issues:
```bash
python3 authenticate_[platform].py
```

### Watcher Not Finding Items

1. Check logs: `Logs/[platform]_watcher.log`
2. Platform UI may have changed - selectors need updating
3. Try running in visible mode (headless=False) to see what's happening

### Rate Limiting / Account Restrictions

If a platform restricts your account:
1. Stop the watcher immediately
2. Increase check interval (e.g., 900 or 1800 seconds)
3. Verify your account through the platform's process
4. Wait 24-48 hours before restarting

### Browser Crashes

If browser crashes frequently:
1. Update Playwright: `pip install --upgrade playwright`
2. Reinstall browsers: `playwright install chromium`
3. Check system resources (RAM, disk space)

## Security & Privacy

### What's Stored Locally

- **Session cookies**: In `*_session/` directories
- **Processed IDs**: In `*_processed.json` files
- **Logs**: In `Logs/` directory
- **Action files**: In `Needs_Action/` directory

### What's NOT Stored

- Passwords (never stored)
- Full message history (only recent items checked)
- Media files (only text content)

### Best Practices

1. **Keep sessions secure**: Don't share `*_session/` directories
2. **Use 2FA**: Enable two-factor authentication on all platforms
3. **Regular re-authentication**: Re-authenticate every few weeks
4. **Monitor logs**: Check for suspicious activity
5. **Reasonable intervals**: Don't check too frequently

## Terms of Service Considerations

⚠️ **Important**: Browser automation may violate platform Terms of Service:

- **Facebook**: May restrict accounts using automation
- **Instagram**: Actively detects and restricts automation
- **Twitter/X**: May suspend accounts for automation
- **LinkedIn**: May limit account access
- **WhatsApp**: Generally more tolerant but still monitors

**Use at your own risk** for:
- Personal use only
- Educational purposes
- Testing and development

**Not recommended for**:
- Commercial use
- High-frequency monitoring
- Automated posting/actions

## Integration with AI Employee System

These watchers integrate with your AI Employee Vault:

1. **Watchers** → Create files in `Needs_Action/`
2. **Planning Loop** → Processes files, creates plans in `Plans/`
3. **Approval Workflow** → Plans move to `Pending_Approval/`
4. **Execution** → Approved plans executed, results in `Done/`

## Advanced: Running on Startup

### Linux/WSL (systemd)

Create service file: `/etc/systemd/system/ai-watchers.service`

```ini
[Unit]
Description=AI Employee Watchers
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/AI_Employee_Vault/Automation/watchers
ExecStart=/usr/bin/python3 run_all_watchers.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-watchers
sudo systemctl start ai-watchers
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start a program
5. Program: `python3`
6. Arguments: `run_all_watchers.py`
7. Start in: `C:\path\to\Automation\watchers`

## Performance Considerations

### Resource Usage

Each watcher uses:
- **Memory**: ~200-300 MB per browser instance
- **CPU**: Minimal when idle, spikes during checks
- **Disk**: ~100 MB per session directory

**Total for 6 watchers**: ~1.5-2 GB RAM

### Optimization Tips

1. **Increase intervals**: Longer intervals = less resource usage
2. **Disable unused watchers**: Only run what you need
3. **Headless mode**: Always use headless=True in production
4. **Close other browsers**: Avoid running multiple Chrome instances

## Summary

You now have a complete social media monitoring system that:

✅ Monitors 6 platforms using your real accounts
✅ No API keys or costs required
✅ Runs continuously in the background
✅ Creates action files for important items
✅ Integrates with your AI Employee workflow
✅ Respects your privacy (all data stays local)

## Quick Reference Commands

```bash
# Authenticate platforms
python3 authenticate_facebook.py
python3 authenticate_instagram.py
python3 authenticate_twitter.py

# Test individual watchers
python3 facebook_watcher.py
python3 instagram_watcher.py
python3 twitter_watcher.py

# Run all watchers
python3 run_all_watchers.py

# View logs
tail -f Logs/facebook_watcher.log
tail -f Logs/instagram_watcher.log
tail -f Logs/twitter_watcher.log
```

## Next Steps

1. ✅ Authenticate all platforms
2. ✅ Test each watcher individually
3. ✅ Run all watchers together
4. Customize keywords for your needs
5. Monitor logs to ensure everything works
6. Integrate with planning loop for automated responses
7. Set up to run on startup (optional)

## Support

For detailed platform-specific guides, see:
- `FACEBOOK_SETUP_GUIDE.md`
- `INSTAGRAM_SETUP_GUIDE.md`
- `TWITTER_SETUP_GUIDE.md`
- `WHATSAPP_AUTH_GUIDE.md` (if exists)

For issues, check the logs in `Logs/` directory.
