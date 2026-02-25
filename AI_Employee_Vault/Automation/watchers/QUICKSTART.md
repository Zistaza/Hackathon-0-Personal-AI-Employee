# AI Employee Watchers - Quick Start Guide

## Installation (5 minutes)

```bash
cd Automation/watchers
./setup.sh
```

This installs all dependencies and prepares the environment.

## First Run Setup

### 1. Gmail Watcher (2 minutes)

```bash
python3 gmail_watcher.py
```

- Browser opens automatically
- Login to Google account
- Grant Gmail API permissions
- Token saved to `gmail_token.pickle`
- Press Ctrl+C to stop

### 2. WhatsApp Watcher (1 minute)

```bash
python3 whatsapp_watcher.py
```

- Browser opens with WhatsApp Web
- Scan QR code with your phone
- Session saved to `whatsapp_session/`
- Press Ctrl+C to stop

### 3. LinkedIn Watcher (1 minute)

```bash
python3 linkedin_watcher.py
```

- Browser opens with LinkedIn
- Login manually
- Session saved to `linkedin_session/`
- Press Ctrl+C to stop

## Run All Watchers

```bash
python3 run_all_watchers.py
```

All three watchers run continuously in separate processes.

## Check Status

```bash
python3 check_status.py
```

Shows:
- Processed item counts
- Session status
- Recent log entries
- Files in Needs_Action

## Stop Watchers

Press `Ctrl+C` in the terminal running the watchers.

## Run as Background Service

### Option 1: Using nohup

```bash
nohup python3 run_all_watchers.py > watcher.log 2>&1 &
```

### Option 2: Using screen

```bash
screen -S watchers
python3 run_all_watchers.py
# Press Ctrl+A, then D to detach
# Reattach: screen -r watchers
```

### Option 3: Using systemd (Linux)

```bash
# Copy service file
sudo cp ai-employee-watchers.service /etc/systemd/system/

# Edit service file with your username
sudo nano /etc/systemd/system/ai-employee-watchers.service

# Enable and start
sudo systemctl enable ai-employee-watchers
sudo systemctl start ai-employee-watchers

# Check status
sudo systemctl status ai-employee-watchers

# View logs
sudo journalctl -u ai-employee-watchers -f
```

## Configuration

Edit `config.json` to customize:

```json
{
  "watchers": {
    "gmail": {
      "enabled": true,
      "check_interval": 300,
      "keywords": ["invoice", "urgent", "payment"]
    }
  }
}
```

## Troubleshooting

### Gmail: "credentials.json not found"

Place `credentials.json` in project root:
```
AI_Employee_Vault/credentials.json
```

### WhatsApp: "QR code timeout"

Increase timeout or try again. Ensure phone has internet.

### LinkedIn: "Login required every time"

Check `linkedin_session/` permissions. LinkedIn may require periodic re-auth.

### Check Logs

```bash
# View recent logs
tail -f ../../Logs/gmail_watcher.log
tail -f ../../Logs/whatsapp_watcher.log
tail -f ../../Logs/linkedin_watcher.log
```

## What Happens Next

1. **Watchers monitor** Gmail, WhatsApp, LinkedIn
2. **Keyword matches** create files in `/Needs_Action`
3. **process_needs_action** skill processes files
4. **Plans created** with risk analysis
5. **Human reviews** in `/Pending_Approval`
6. **Actions executed** after approval

## File Format

Created files in `/Needs_Action`:

```markdown
---
type: gmail
sender: john@example.com
subject: Invoice for January
timestamp: 2026-02-23T10:30:00Z
status: pending
---

**Subject:** Invoice for January

**From:** john@example.com

**Message:**
Please find attached the invoice for January services.
```

## Performance

- **Gmail**: ~50MB RAM, <1% CPU (idle)
- **WhatsApp**: ~200MB RAM, 2-5% CPU (idle)
- **LinkedIn**: ~200MB RAM, 2-5% CPU (idle)

## Security

- Never commit session files
- Protect credentials.json (chmod 600)
- Use environment variables for sensitive config
- Monitor logs for suspicious activity

## Support

1. Check `README.md` for detailed documentation
2. Run `python3 check_status.py` for diagnostics
3. Review logs in `/Logs/`
4. Verify authentication and permissions

## Next Steps

After watchers are running:

1. **Test**: Send yourself a test email/message with keywords
2. **Verify**: Check `/Needs_Action` for created files
3. **Monitor**: Run `check_status.py` periodically
4. **Integrate**: Ensure `process_needs_action` skill is running
5. **Optimize**: Adjust check intervals and keywords as needed

---

**Version**: 1.0
**Last Updated**: 2026-02-23
