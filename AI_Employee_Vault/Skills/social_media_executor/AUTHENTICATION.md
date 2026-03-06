# LinkedIn Authentication Setup

## Quick Start

Run the authentication script to log in to LinkedIn and save your session:

```bash
cd /mnt/c/Users/Tesla\ Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault/Skills/social_media_executor
python3 authenticate.py
```

## What This Does

1. Opens a browser window with LinkedIn
2. Waits for you to manually log in
3. Saves your authenticated session to `/Sessions/linkedin/`
4. Verifies authentication was successful

## Step-by-Step Instructions

### 1. Run the Authentication Script

```bash
python3 authenticate.py
```

### 2. Log In to LinkedIn

- A browser window will open automatically
- Navigate to LinkedIn and log in with your credentials
- Complete any 2FA/verification if required
- Wait until you see your LinkedIn feed

### 3. Confirm Authentication

- Once you're logged in and can see your feed, return to the terminal
- Press ENTER to save the session
- The script will verify authentication and close the browser

### 4. Test Automated Posting

After authentication, test with a simple post:

```bash
# Create a test post file
cat > /mnt/c/Users/Tesla\ Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault/Approved/POST_linkedin_test.md << 'EOF'
---
platform: linkedin
type: post
scheduled: false
---

Testing automated LinkedIn posting! 🚀
EOF
```

The ApprovedFolderMonitor will automatically detect and post it within 30 seconds.

## Session Persistence

Your LinkedIn session is saved in:
```
/Sessions/linkedin/
```

This directory contains:
- Browser cookies
- Local storage
- Session data

The session persists across restarts, so you only need to authenticate once (unless LinkedIn logs you out).

## Troubleshooting

### "Not logged in" Error

If you see this error after authentication:
1. Run `authenticate.py` again
2. Make sure you're fully logged in (can see your feed)
3. Check that cookies are being saved to `/Sessions/linkedin/`

### Session Expired

LinkedIn may expire sessions after some time. If posts fail with "Not logged in":
1. Run `authenticate.py` again to refresh the session
2. Consider enabling "Remember me" when logging in

### Browser Not Opening

If the browser doesn't open:
1. Check that Playwright is installed: `playwright install chromium`
2. Verify you're running on a system with display support (not headless server)
3. Check the config.json `headless` setting is `false`

## Security Notes

- Your LinkedIn credentials are NOT stored by this script
- Only browser session data is saved locally
- Session files are stored in `/Sessions/linkedin/` - keep this directory secure
- Never commit session files to version control

## Next Steps

After authentication:
1. Test posting manually with the test post above
2. Set up scheduled posts in `/Pending_Approval/`
3. Monitor execution in PM2 logs: `pm2 logs orchestrator`
