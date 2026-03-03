# Twitter/X Watcher Setup Guide

This guide will help you set up the Twitter/X watcher to monitor your real Twitter/X account for notifications and direct messages.

## Overview

The Twitter/X watcher uses browser automation (Playwright) to access your Twitter/X account. It monitors:
- **Notifications**: Mentions, replies, likes, retweets, follows
- **Direct Messages**: New DMs from your Twitter/X inbox

## Prerequisites

1. **Playwright installed**:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **A Twitter/X account** that you want to monitor

## Step 1: Authenticate with Twitter/X

Run the authentication script to log in and save your session:

```bash
cd Automation/watchers
python3 authenticate_twitter.py
```

**What happens:**
1. A browser window will open
2. Log in to Twitter/X with your credentials
3. Complete any 2FA/security checks if prompted
4. Wait for the home timeline to load
5. The script will detect when you're logged in
6. Your session will be saved to `twitter_session/` directory

**Important**: Twitter/X may ask for additional verification - complete all steps.

## Step 2: Test the Twitter/X Watcher

Test that the watcher works with your account:

```bash
python3 twitter_watcher.py
```

**What it does:**
- Checks Twitter/X notifications
- Checks direct messages
- Creates markdown files in `Needs_Action/` for items matching keywords
- Runs every 10 minutes by default

**Keywords monitored** (configurable):
- urgent
- important
- mention
- dm
- message

Press `Ctrl+C` to stop the watcher.

## Step 3: Run All Watchers Together

Once Twitter/X authentication works, run all watchers together:

```bash
python3 run_all_watchers.py
```

This will start:
- Gmail watcher
- WhatsApp watcher
- LinkedIn watcher
- Facebook watcher
- Instagram watcher
- **Twitter/X watcher** (new!)

All watchers run in separate processes and monitor continuously.

## Configuration

### Change Check Interval

Edit `twitter_watcher.py` or `run_all_watchers.py`:

```python
check_interval=600,  # 600 seconds = 10 minutes
```

### Change Keywords

Edit the keywords list:

```python
keywords=["urgent", "important", "mention", "dm", "message", "custom_keyword"]
```

### Disable Notifications or Messages

```python
monitor_notifications=True,  # Set to False to disable
monitor_messages=True,       # Set to False to disable
```

## How It Works

1. **Browser Automation**: Uses Playwright to control a real Chrome browser
2. **Session Persistence**: Saves cookies/session in `twitter_session/` directory
3. **Headless Mode**: After first authentication, runs in background (headless=True)
4. **Event Detection**: Scrapes notifications and DMs from Twitter/X's web interface
5. **Keyword Filtering**: Only creates action files for items containing your keywords
6. **Duplicate Prevention**: Tracks processed items to avoid duplicates

## Output Files

When a notification or message matches your keywords, a markdown file is created:

**Location**: `Needs_Action/twitter_TIMESTAMP.md`

**Format**:
```markdown
---
type: twitter_notification
timestamp: 2026-03-03T10:30:00Z
status: pending
---

[Notification or message content here]
```

## Troubleshooting

### "NO TWITTER/X SESSION FOUND"
- Run `python3 authenticate_twitter.py` first
- Make sure you complete the login process

### "Login timeout"
- Twitter/X may require additional verification
- Try running authentication script again
- Check if Twitter/X is blocking automated access

### Watcher not finding notifications/messages
- Twitter/X's HTML structure changes frequently
- The selectors in the code may need updating
- Check logs in `Logs/twitter_watcher.log`

### Session expired
- Twitter/X sessions can expire after some time
- Re-run `python3 authenticate_twitter.py` to refresh

### "Suspicious Activity" warning
- Twitter/X may flag automated access
- Verify it's you through email/SMS
- Consider using less frequent check intervals

### Rate limiting
- Twitter/X rate limits automated access
- Increase `check_interval` to 900 (15 minutes) or more
- Don't run multiple instances simultaneously

## Security Notes

⚠️ **Important Security Considerations**:

1. **Session Storage**: Your Twitter/X session is stored locally in `twitter_session/`
   - Keep this directory secure
   - Don't commit it to git (already in .gitignore)

2. **Automation Detection**: Twitter/X detects and may restrict automation
   - Use reasonable check intervals (10+ minutes minimum)
   - Don't perform actions too quickly
   - Twitter/X may temporarily restrict your account

3. **Terms of Service**: Browser automation may violate Twitter/X's ToS
   - Use at your own risk
   - For personal/educational use only
   - Your account could be restricted or suspended

4. **Two-Factor Authentication**: Highly recommended
   - You'll need to complete 2FA during authentication
   - Session will be saved after successful 2FA

## Twitter/X-Specific Considerations

Twitter/X actively monitors for automation:

- **Frequent session expiration**: May need to re-authenticate regularly
- **Rate limits**: Keep check intervals at 10+ minutes
- **Account restrictions**: Twitter/X may temporarily restrict your account if it detects automation
- **Verification challenges**: May ask you to verify your identity periodically

**Recommendation**: Use Twitter/X watcher carefully with longer intervals than other watchers.

## Advanced Usage

### Run in Foreground (for debugging)

Edit `run_all_watchers.py` and change:
```python
headless=False,  # Shows browser window
```

### Custom Session Directory

```python
watcher = TwitterWatcher(
    user_data_dir="./my_custom_twitter_session"
)
```

### Monitor Only Notifications (Skip Messages)

```python
monitor_notifications=True,
monitor_messages=False
```

## Complete Social Media Monitoring

You now have watchers for all major platforms:
- ✓ Gmail
- ✓ WhatsApp
- ✓ LinkedIn
- ✓ Facebook
- ✓ Instagram
- ✓ Twitter/X

## Authentication Summary

To set up all social media watchers:

```bash
cd Automation/watchers

# Authenticate each platform
python3 authenticate_facebook.py
python3 authenticate_instagram.py
python3 authenticate_twitter.py

# Test individual watchers
python3 facebook_watcher.py
python3 instagram_watcher.py
python3 twitter_watcher.py

# Run all watchers together
python3 run_all_watchers.py
```

## Next Steps

1. Customize keywords for each platform based on your needs
2. Integrate with the planning loop for automated responses
3. Set up the system to run on startup
4. Monitor logs to ensure watchers are working correctly

## Support

If you encounter issues:
1. Check `Logs/twitter_watcher.log` for detailed error messages
2. Verify Playwright is installed correctly
3. Try re-authenticating with Twitter/X
4. Check if Twitter/X's UI has changed (may need code updates)
5. Consider using longer check intervals if getting rate limited or restricted
