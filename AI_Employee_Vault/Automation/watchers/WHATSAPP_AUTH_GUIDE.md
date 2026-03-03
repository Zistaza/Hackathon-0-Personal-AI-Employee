# WhatsApp Watcher - Authentication & Troubleshooting

## Current Status
The WhatsApp watcher crash loop has been fixed with the following improvements:

### Fixes Applied:
1. **Watcher Manager** - Now properly restarts crashed processes automatically
2. **WhatsApp Watcher** - Added session validation to prevent headless mode without authentication
3. **Event Loop Handling** - Fixed async/await issues that caused crashes

## Authentication Required

The WhatsApp watcher requires authentication before it can run in headless mode.

### Option 1: Authenticate from Windows (Recommended)

Since you're running WSL, the easiest way is to authenticate from Windows:

1. Open PowerShell or Command Prompt on Windows
2. Navigate to the watchers directory:
   ```
   cd "C:\Users\Tesla Laptops\Desktop\AI_Employee_Vault\AI_Employee_Vault\Automation\watchers"
   ```
3. Install playwright (if not already installed):
   ```
   pip install playwright
   playwright install chromium
   ```
4. Run the authentication script:
   ```
   python authenticate_whatsapp_windows.py
   ```
5. Scan the QR code with your phone when the browser opens
6. Wait for "Authentication successful" message

### Option 2: Authenticate from WSL with X Server

If you have an X server (like VcXsrv) running on Windows:

1. Set DISPLAY environment variable:
   ```bash
   export DISPLAY=:0
   ```
2. Run the authentication script:
   ```bash
   cd /mnt/c/Users/Tesla\ Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault/Automation/watchers
   python3 authenticate_whatsapp.py
   ```

### Option 3: Disable WhatsApp Watcher Temporarily

If you don't need WhatsApp monitoring right now, you can disable it:

Edit `run_all_watchers.py` and comment out the WhatsApp watcher section (lines 63-74).

## Verify Authentication

After authenticating, test the session:

```bash
cd /mnt/c/Users/Tesla\ Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault/Automation/watchers
python3 test_whatsapp_session.py
```

You should see: "✓ Session is valid - WhatsApp is authenticated"

## Start the Watchers

Once authenticated, start all watchers:

```bash
cd /mnt/c/Users/Tesla\ Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault/Automation/watchers
python3 run_all_watchers.py
```

The watcher manager will now automatically restart any crashed watchers.

## Troubleshooting

### Watcher still crashing?
- Check logs: `tail -f ../../Logs/whatsapp_watcher.log`
- Verify session: `python3 test_whatsapp_session.py`
- Re-authenticate if session expired

### Can't see browser window?
- Use Option 1 (authenticate from Windows directly)
- Or install X server for WSL

### Session keeps expiring?
- WhatsApp sessions can expire if not used regularly
- Re-authenticate when needed
- Consider keeping the watcher running continuously
