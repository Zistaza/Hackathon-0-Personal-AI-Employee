# Bronze Tier AI Employee - Quick Start Guide

## System Overview

Your Bronze Tier Personal AI Employee is now fully operational with automated file processing.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start the Filesystem Watcher

```bash
python3 filesystem_watcher.py
```

### Step 3: Test the System

Drop a file in `/Inbox` and watch it automatically move to `/Needs_Action`:

```bash
echo "# Test Task\n\nThis is a test task for the AI Employee." > Inbox/test-task.md
```

---

## 📁 Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md              # System status and activity
├── Company_Handbook.md       # Operating rules and workflows
├── filesystem_watcher.py     # Automated file monitoring
├── requirements.txt          # Python dependencies
│
├── Inbox/                    # Drop files here
├── Needs_Action/             # Files awaiting processing
├── Plans/                    # Generated execution plans
├── Pending_Approval/         # Plans awaiting your review
├── Approved/                 # Approved plans
├── Rejected/                 # Rejected plans with feedback
├── Done/                     # Completed work archive
├── Logs/                     # System activity logs
│   └── README.md
└── Skills/                   # AI Employee capabilities
    └── process_needs_action/
        └── SKILL.md
```

---

## 🔄 Complete Workflow

### Automated Flow

1. **You** → Drop file in `/Inbox`
2. **Watcher** → Automatically moves to `/Needs_Action`
3. **AI Employee** → Analyzes file and creates plan
4. **AI Employee** → Moves plan to `/Pending_Approval`
5. **You** → Review and approve/reject plan
6. **AI Employee** → Executes approved plan
7. **System** → Archives to `/Done` with logs

### Manual Trigger

To manually process files in `/Needs_Action`:

```
Use process_needs_action to process all files in /Needs_Action
```

---

## 📋 Common Tasks

### View System Status
Open `Dashboard.md` in Obsidian

### Check Recent Activity
```bash
cat Logs/$(date +%Y-%m-%d).json
```

### View Pending Approvals
```bash
ls -la Pending_Approval/
```

### Review Completed Work
```bash
ls -la Done/
```

---

## 🛠️ Running the Watcher

### Foreground (for testing)
```bash
python3 filesystem_watcher.py
```
Press `Ctrl+C` to stop

### Background (for production)

**Mac/Linux:**
```bash
nohup python3 filesystem_watcher.py > watcher.out 2>&1 &
```

**Windows:**
```powershell
Start-Process python -ArgumentList "filesystem_watcher.py" -WindowStyle Hidden
```

See `FILESYSTEM_WATCHER_GUIDE.md` for permanent service setup.

---

## 📊 Monitoring

### Check Watcher Status
```bash
tail -f filesystem_watcher.log
```

### View Today's Activity
```bash
cat Logs/$(date +%Y-%m-%d).json | python3 -m json.tool
```

### Count Pending Items
```bash
ls -1 Needs_Action/*.md 2>/dev/null | wc -l
```

---

## 🔒 Safety Features

- ✓ No automatic file deletion
- ✓ Duplicate filename handling
- ✓ Complete audit trail in logs
- ✓ Graceful error recovery
- ✓ Human approval required for plans
- ✓ Idempotent operations

---

## 📚 Documentation

- `Company_Handbook.md` - Operating principles and rules
- `FILESYSTEM_WATCHER_GUIDE.md` - Detailed watcher documentation
- `Skills/process_needs_action/SKILL.md` - Processing workflow details
- `Logs/README.md` - Log format specification

---

## 🆘 Troubleshooting

### Watcher not starting?
```bash
pip install --upgrade watchdog
python3 filesystem_watcher.py
```

### Files not moving?
1. Check watcher is running
2. Verify file is in `/Inbox`
3. Check `filesystem_watcher.log`

### Need help?
1. Review `FILESYSTEM_WATCHER_GUIDE.md`
2. Check `filesystem_watcher.log` for errors
3. Verify folder permissions

---

## 🎯 Next Steps

1. **Start the watcher**: `python3 filesystem_watcher.py`
2. **Test with a file**: Drop a markdown file in `/Inbox`
3. **Watch it work**: See it move to `/Needs_Action`
4. **Process files**: Use the `process_needs_action` skill
5. **Review plans**: Check `/Pending_Approval`
6. **Approve/reject**: Move plans to `/Approved` or `/Rejected`

---

## 📈 System Status

**Tier**: Bronze - Foundation Mode
**Status**: Fully Operational
**Automation**: Filesystem Watcher + Process Needs Action Skill
**Safety**: Production-Ready with Error Handling

Your Bronze Tier Personal AI Employee is ready to work!
