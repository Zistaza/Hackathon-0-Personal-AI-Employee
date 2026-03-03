# Instagram Watcher Setup Guide

This guide will help you set up the Instagram watcher to monitor your real Instagram account for notifications and direct messages.

## Overview

The Instagram watcher uses browser automation (Playwright) to access your Instagram account. It monitors:
- **Notifications**: New Instagram notifications (likes, comments, follows, mentions)
- **Direct Messages**: New DMs from your Instagram inbox

## Prerequisites

1. **Playwright installed**:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **An Instagram account** that you want to monitor

## Step 1: Authenticate with Instagram

Run the authentication script to log in and save your session:

```bash
cd Automation/watchers
python3 authenticate_instagram.py
```

**What happens:**
1. A browser window will open
2. Log in to Instagram with your credentials
3. Complete any 2FA/security checks if prompted
4. Click "Save Your Login Info" if prompted (recommended)
5. The script will detect when you're logged in
6. Your session will be saved to `instagram_session/` directory

**Important**: Instagram may ask you to verify it's you - complete any verification steps.

## Step 2: Test the Instagram Watcher

Test that the watcher works with your account:

```bash
python3 instagram_watcher.py
```

**What it does:**
- Checks Instagram notifications
- Checks direct messages
- Creates markdown files in `Needs_Action/` for items matching keywords
- Runs every 10 minutes by default

**Keywords monitored** (configurable):
- urgent
- important
- collab
- partnership
- business

Press `Ctrl+C` to stop the watcher.

## Step 3: Run All Watchers Together

Once Instagram authentication works, run all watchers together:

```bash
python3 run_all_watchers.py
```

This will start:
- Gmail watcher
- WhatsApp watcher
- LinkedIn watcher
- Facebook watcher
- **Instagram watcher** (new!)

All watchers run in separate processes and monitor continuously.

## Configuration

### Change Check Interval

Edit `instagram_watcher.py` or `run_all_watchers.py`:

```python
check_interval=600,  # 600 seconds = 10 minutes
```

### Change Keywords

Edit the keywords list:

```python
keywords=["urgent", "important", "collab", "partnership", "business", "custom_keyword"]
```

### Disable Notifications or Messages

```python
monitor_notifications=True,  # Set to False to disable
monitor_messages=True,       # Set to False to disable
```

## How It Works

1. **Browser Automation**: Uses Playwright to control a real Chrome browser
2. **Session Persistence**: Saves cookies/session in `instagram_session/` directory
3. **Headless Mode**: After first authentication, runs in background (headless=True)
4. **Event Detection**: Scrapes notifications and DMs from Instagram's web interface
5. **Keyword Filtering**: Only creates action files for items containing your keywords
6. **Duplicate Prevention**: Tracks processed items to avoid duplicates

## Output Files

When a notification or message matches your keywords, a markdown file is created:

**Location**: `Needs_Action/instagram_TIMESTAMP.md`

**Format**:
```markdown
---
type: instagram_notification
timestamp: 2026-03-03T10:30:00Z
status: pending
---

[Notification or message content here]
```

## Troubleshooting

### "NO INSTAGRAM SESSION FOUND"
- Run `python3 authenticate_instagram.py` first
- Make sure you complete the login process

### "Login timeout"
- Instagram may require additional verification
- Try running authentication script again
- Check if Instagram is blocking automated access

### Watcher not finding notifications/messages
- Instagram's HTML structure changes frequently
- The selectors in the code may need updating
- Check logs in `Logs/instagram_watcher.log`

### Session expired
- Instagram sessions can expire after some time
- Re-run `python3 authenticate_instagram.py` to refresh

### "Suspicious Login Attempt" warning
- Instagram may flag automated access
- Verify it's you through email/SMS
- Consider using less frequent check intervals

### Rate limiting
- Instagram aggressively rate limits automated access
- Increase `check_interval` to 900 (15 minutes) or more
- Don't run multiple instances simultaneously

## Security Notes

⚠️ **Important Security Considerations**:

1. **Session Storage**: Your Instagram session is stored locally in `instagram_session/`
   - Keep this directory secure
   - Don't commit it to git (already in .gitignore)

2. **Automation Detection**: Instagram actively detects and blocks automation
   - Use reasonable check intervals (10+ minutes minimum)
   - Don't perform actions too quickly
   - Instagram may temporarily restrict your account

3. **Terms of Service**: Browser automation violates Instagram's ToS
   - Use at your own risk
   - For personal/educational use only
   - Your account could be restricted or banned

4. **Two-Factor Authentication**: Highly recommended
   - You'll need to complete 2FA during authentication
   - Session will be saved after successful 2FA

## Instagram-Specific Considerations

Instagram is more aggressive than Facebook about detecting automation:

- **More frequent session expiration**: May need to re-authenticate weekly
- **Stricter rate limits**: Keep check intervals at 10+ minutes
- **Action blocks**: Instagram may temporarily block your account if it detects automation
- **Verification challenges**: May ask you to verify your identity periodically

**Recommendation**: Use Instagram watcher sparingly and with longer intervals than other watchers.

## Advanced Usage

### Run in Foreground (for debugging)

Edit `run_all_watchers.py` and change:
```python
headless=False,  # Shows browser window
```

### Custom Session Directory

```python
watcher = InstagramWatcher(
    user_data_dir="./my_custom_instagram_session"
)
```

### Monitor Only Messages (Skip Notifications)

```python
monitor_notifications=False,
monitor_messages=True
```

## Next Steps

After setting up Instagram, you now have watchers for:
- ✓ Gmail
- ✓ WhatsApp
- ✓ LinkedIn
- ✓ Facebook
- ✓ Instagram

Consider:
1. Adding Twitter/X watcher (similar process)
2. Customizing keywords for each platform
3. Integrating with the planning loop for automated responses
4. Setting up the system to run on startup

## Support

If you encounter issues:
1. Check `Logs/instagram_watcher.log` for detailed error messages
2. Verify Playwright is installed correctly
3. Try re-authenticating with Instagram
4. Check if Instagram's UI has changed (may need code updates)
5. Consider using longer check intervals if getting rate limited
