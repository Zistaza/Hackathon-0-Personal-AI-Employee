# Filesystem Watcher - Installation & Usage Guide

## Overview

The Filesystem Watcher automatically monitors the `/Inbox` folder in your Bronze Tier AI Employee vault and moves new files to `/Needs_Action` for processing.

---

## Prerequisites

### Python Installation

**Check if Python is installed:**
```bash
python --version
# or
python3 --version
```

You need Python 3.7 or higher.

**If Python is not installed:**

- **Windows**: Download from [python.org](https://www.python.org/downloads/)
  - During installation, check "Add Python to PATH"

- **Mac**:
  ```bash
  brew install python3
  ```
  Or download from [python.org](https://www.python.org/downloads/)

- **Linux**:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip
  ```

---

## Installation

### Step 1: Install Required Library

Open your terminal/command prompt and run:

```bash
pip install watchdog
```

Or if using Python 3 specifically:

```bash
pip3 install watchdog
```

**Verify installation:**
```bash
pip show watchdog
```

You should see version information for the watchdog package.

---

## Running the Watcher

### Option 1: Run from Vault Directory (Recommended)

Navigate to your vault directory and run:

```bash
# Windows
cd D:\Apps\AI_Employee_Vault
python filesystem_watcher.py

# Mac/Linux
cd /path/to/AI_Employee_Vault
python3 filesystem_watcher.py
```

### Option 2: Run from Any Directory

Specify the vault path as an argument:

```bash
# Windows
python filesystem_watcher.py "D:\Apps\AI_Employee_Vault"

# Mac
python3 filesystem_watcher.py "/Users/username/AI_Employee_Vault"

# Linux
python3 filesystem_watcher.py "/home/username/AI_Employee_Vault"
```

### Expected Output

When successfully started, you'll see:

```
============================================================
Bronze Tier AI Employee - Filesystem Watcher
============================================================
Vault: /path/to/AI_Employee_Vault
Watching: /path/to/AI_Employee_Vault/Inbox
Press Ctrl+C to stop
============================================================
✓ Watcher started successfully

✓ Filesystem watcher is running...
✓ Monitoring: /path/to/AI_Employee_Vault/Inbox
✓ Press Ctrl+C to stop
```

When a file is detected and moved:

```
[14:23:45] Moved: new-task.md → /Needs_Action/
```

---

## Testing the Watcher

### Test 1: Basic File Movement

1. Start the watcher
2. Create a new file in `/Inbox`:
   ```bash
   echo "Test task" > Inbox/test-task.md
   ```
3. Watch the console output - you should see:
   ```
   [HH:MM:SS] Moved: test-task.md → /Needs_Action/
   ```
4. Verify the file is now in `/Needs_Action`

### Test 2: Duplicate Filename Handling

1. Create a file in `/Needs_Action`:
   ```bash
   echo "Existing" > Needs_Action/duplicate.md
   ```
2. Create the same filename in `/Inbox`:
   ```bash
   echo "New" > Inbox/duplicate.md
   ```
3. The watcher should rename it to `duplicate_1.md`

### Test 3: Multiple Files

1. Create several files at once:
   ```bash
   echo "Task 1" > Inbox/task1.md
   echo "Task 2" > Inbox/task2.md
   echo "Task 3" > Inbox/task3.md
   ```
2. All should be moved automatically

---

## Stopping the Watcher

Press `Ctrl+C` in the terminal where the watcher is running.

You'll see:
```
Stopping filesystem watcher...
✓ Watcher stopped gracefully
```

---

## Running as a Background Service

### Windows - Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "AI Employee Watcher"
4. Trigger: "When I log on"
5. Action: "Start a program"
6. Program: `python`
7. Arguments: `filesystem_watcher.py`
8. Start in: `D:\Apps\AI_Employee_Vault`

### Mac - launchd

Create file: `~/Library/LaunchAgents/com.ai-employee.watcher.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ai-employee.watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/AI_Employee_Vault/filesystem_watcher.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ai-employee-watcher.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ai-employee-watcher.error.log</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.ai-employee.watcher.plist
```

### Linux - systemd

Create file: `/etc/systemd/system/ai-employee-watcher.service`

```ini
[Unit]
Description=AI Employee Filesystem Watcher
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/AI_Employee_Vault
ExecStart=/usr/bin/python3 /path/to/AI_Employee_Vault/filesystem_watcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-employee-watcher
sudo systemctl start ai-employee-watcher
sudo systemctl status ai-employee-watcher
```

---

## Logging

The watcher creates a log file: `filesystem_watcher.log`

**View recent logs:**
```bash
# Last 20 lines
tail -20 filesystem_watcher.log

# Follow in real-time
tail -f filesystem_watcher.log
```

**Log entries include:**
- Startup/shutdown events
- Files detected and moved
- Errors and warnings
- Timestamp for each event

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'watchdog'"

**Solution:** Install watchdog library
```bash
pip install watchdog
```

### Issue: "Inbox folder not found"

**Solution:** Ensure you're running from the correct directory or provide the vault path:
```bash
python filesystem_watcher.py "/full/path/to/vault"
```

### Issue: "Permission denied"

**Solution:**
- Check file permissions on Inbox and Needs_Action folders
- On Mac/Linux, ensure you have write permissions:
  ```bash
  chmod 755 Inbox Needs_Action
  ```

### Issue: Files not being detected

**Solution:**
1. Check the watcher is running (look for console output)
2. Verify you're adding files to the correct `/Inbox` folder
3. Check `filesystem_watcher.log` for errors
4. Ensure files are not hidden (don't start with `.`)

### Issue: Watcher crashes or stops

**Solution:**
1. Check `filesystem_watcher.log` for error messages
2. Ensure Python version is 3.7+
3. Reinstall watchdog: `pip install --upgrade watchdog`
4. Run with verbose output to see detailed errors

---

## Safety Features

The watcher includes several safety mechanisms:

1. **No Overwrites**: If a file with the same name exists in `/Needs_Action`, it's renamed with a counter (e.g., `file_1.md`)

2. **Write Completion Detection**: Waits for files to finish being written before moving them

3. **Error Recovery**: Continues running even if individual file operations fail

4. **Graceful Shutdown**: Properly cleans up when stopped with Ctrl+C

5. **Ignore Hidden Files**: Skips files starting with `.` or `~`

6. **Comprehensive Logging**: All operations are logged for audit trail

---

## Performance Notes

- **CPU Usage**: Minimal (event-driven, not polling)
- **Memory Usage**: ~10-20 MB
- **Latency**: Files detected within 1 second
- **Scalability**: Handles hundreds of files efficiently

---

## Integration with Bronze Tier Workflow

The watcher is the first step in the automated workflow:

1. **User** → Drops file in `/Inbox`
2. **Watcher** → Moves to `/Needs_Action`
3. **process_needs_action skill** → Analyzes and creates plan
4. **Human** → Reviews and approves plan
5. **Execution** → Plan is executed

---

## Support

For issues or questions:
1. Check `filesystem_watcher.log` for error details
2. Verify all prerequisites are installed
3. Test with a simple file first
4. Review the troubleshooting section above
