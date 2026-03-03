# Facebook Watcher Setup Guide

This guide will help you set up the Facebook watcher to monitor your real Facebook account for notifications and messages.

## Overview

The Facebook watcher uses browser automation (Playwright) to access your Facebook account, just like the WhatsApp and LinkedIn watchers. It monitors:
- **Notifications**: New notifications on Facebook
- **Messages**: New Messenger messages

## Prerequisites

1. **Playwright installed**:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **A Facebook account** that you want to monitor

## Step 1: Authenticate with Facebook

Run the authentication script to log in and save your session:

```bash
cd Automation/watchers
python authenticate_facebook.py
```

**What happens:**
1. A browser window will open
2. Log in to Facebook with your credentials
3. Complete any 2FA/security checks if prompted
4. The script will detect when you're logged in
5. Your session will be saved to `facebook_session/` directory

**Important**: Keep the browser window open until you see "✓ Login successful!"

## Step 2: Test the Facebook Watcher

Test that the watcher works with your account:

```bash
python facebook_watcher.py
```

**What it does:**
- Checks Facebook notifications
- Checks Messenger messages
- Creates markdown files in `Needs_Action/` for items matching keywords
- Runs every 10 minutes by default

**Keywords monitored** (configurable):
- urgent
- important
- invoice
- payment
- proposal

Press `Ctrl+C` to stop the watcher.

## Step 3: Run All Watchers Together

Once Facebook authentication works, run all watchers together:

```bash
python run_all_watchers.py
```

This will start:
- Gmail watcher
- WhatsApp watcher
- LinkedIn watcher
- **Facebook watcher** (new!)

All watchers run in separate processes and monitor continuously.

## Configuration

### Change Check Interval

Edit `facebook_watcher.py` or `run_all_watchers.py`:

```python
check_interval=600,  # 600 seconds = 10 minutes
```

### Change Keywords

Edit the keywords list:

```python
keywords=["urgent", "important", "invoice", "payment", "proposal", "custom_keyword"]
```

### Disable Notifications or Messages

```python
monitor_notifications=True,  # Set to False to disable
monitor_messages=True,       # Set to False to disable
```

## How It Works

1. **Browser Automation**: Uses Playwright to control a real Chrome browser
2. **Session Persistence**: Saves cookies/session in `facebook_session/` directory
3. **Headless Mode**: After first authentication, runs in background (headless=True)
4. **Event Detection**: Scrapes notifications and messages from Facebook's web interface
5. **Keyword Filtering**: Only creates action files for items containing your keywords
6. **Duplicate Prevention**: Tracks processed items to avoid duplicates

## Output Files

When a notification or message matches your keywords, a markdown file is created:

**Location**: `Needs_Action/facebook_TIMESTAMP.md`

**Format**:
```markdown
---
type: facebook_notification
timestamp: 2026-03-03T10:30:00Z
status: pending
---

[Notification or message content here]
```

## Troubleshooting

### "NO FACEBOOK SESSION FOUND"
- Run `python authenticate_facebook.py` first
- Make sure you complete the login process

### "Login timeout"
- Facebook may require additional verification
- Try running authentication script again
- Check if Facebook is blocking automated access

### Watcher not finding notifications
- Facebook's HTML structure changes frequently
- The selectors in the code may need updating
- Check logs in `Logs/facebook_watcher.log`

### Session expired
- Facebook sessions can expire after some time
- Re-run `python authenticate_facebook.py` to refresh

### Rate limiting
- Facebook may rate limit if checking too frequently
- Increase `check_interval` to 900 (15 minutes) or more

## Security Notes

⚠️ **Important Security Considerations**:

1. **Session Storage**: Your Facebook session is stored locally in `facebook_session/`
   - Keep this directory secure
   - Don't commit it to git (already in .gitignore)

2. **Automation Detection**: Facebook may detect browser automation
   - Use reasonable check intervals (10+ minutes)
   - Don't run multiple instances simultaneously

3. **Terms of Service**: Browser automation may violate Facebook's ToS
   - Use at your own risk
   - For personal/educational use only

4. **Two-Factor Authentication**: Recommended for security
   - You'll need to complete 2FA during authentication
   - Session will be saved after successful 2FA

## Advanced Usage

### Run in Foreground (for debugging)

Edit `run_all_watchers.py` and change:
```python
headless=False,  # Shows browser window
```

### Custom Session Directory

```python
watcher = FacebookWatcher(
    user_data_dir="./my_custom_facebook_session"
)
```

### Process Only Unread Items

The watcher attempts to detect unread notifications/messages, but Facebook's UI makes this challenging. Check logs for details.

## Next Steps

After setting up Facebook, you might want to:
1. Set up Twitter/Instagram watchers (similar process)
2. Customize keywords for your specific needs
3. Integrate with the planning loop for automated responses
4. Set up the system to run on startup

## Support

If you encounter issues:
1. Check `Logs/facebook_watcher.log` for detailed error messages
2. Verify Playwright is installed correctly
3. Try re-authenticating with Facebook
4. Check if Facebook's UI has changed (may need code updates)
