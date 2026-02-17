# WSL Users - Use This Version!

## Important: WSL Limitation

The standard `filesystem_watcher.py` uses the `watchdog` library which relies on inotify events. **These events don't work on WSL-mounted Windows drives** (`/mnt/c/`, `/mnt/d/`, etc.).

## Solution: Polling-Based Watcher

Use `filesystem_watcher_polling.py` instead - it works perfectly on WSL!

---

## Quick Start (WSL)

### Step 1: Run the Polling Watcher

```bash
python3 filesystem_watcher_polling.py
```

You'll see:
```
✓ Filesystem watcher is running (polling mode)...
✓ Monitoring: /mnt/d/Apps/AI_Employee_Vault/Inbox
✓ Checking every 2 seconds
✓ Press Ctrl+C to stop
```

### Step 2: Test It

Create a file in Inbox:
```bash
echo "# My Task" > Inbox/my-task.md
```

Within 2 seconds, you'll see:
```
[HH:MM:SS] ✓ Moved: my-task.md → /Needs_Action/
```

---

## How It Works

**Polling Mode**:
- Checks the `/Inbox` folder every 2 seconds
- Detects new files by comparing current files to known files
- Moves new files to `/Needs_Action`
- Ignores files that existed when the watcher started

**Event Mode** (original `filesystem_watcher.py`):
- Uses inotify events (instant detection)
- Only works on native Linux filesystems
- Does NOT work on WSL-mounted Windows drives

---

## Customizing Poll Interval

Default is 2 seconds. To change:

```bash
# Check every 5 seconds
python3 filesystem_watcher_polling.py . 5

# Check every 1 second (faster, more CPU)
python3 filesystem_watcher_polling.py . 1
```

---

## Which Version Should I Use?

| Environment | Use This Version |
|-------------|------------------|
| WSL (Windows Subsystem for Linux) | `filesystem_watcher_polling.py` |
| Native Linux | `filesystem_watcher.py` (faster) |
| macOS | `filesystem_watcher.py` (faster) |
| Windows (native Python) | `filesystem_watcher.py` (faster) |

---

## Running in Background (WSL)

```bash
# Start in background
nohup python3 filesystem_watcher_polling.py > watcher.out 2>&1 &

# Check if running
ps aux | grep filesystem_watcher_polling

# Stop it
pkill -f filesystem_watcher_polling

# View output
tail -f watcher.out
```

---

## Verified Working ✓

The polling version has been tested and confirmed working on WSL with Windows-mounted drives.

**Test Results**:
- ✓ File detection works
- ✓ File movement works
- ✓ Logging works
- ✓ Duplicate filename handling works
- ✓ Graceful shutdown works
