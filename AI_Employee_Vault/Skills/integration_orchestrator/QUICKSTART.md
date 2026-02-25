# Integration Orchestrator - Quick Start

## Installation (2 minutes)

```bash
cd Skills/integration_orchestrator
./setup.sh
```

## Start Orchestrator

```bash
python3 index.py
```

## What It Does

**Monitors:**
- `/Inbox` - New files moved to Needs_Action
- `/Needs_Action` - Triggers process_needs_action skill
- `/Pending_Approval` - Detects approvals, triggers execution

**Triggers:**
- `process_needs_action` - Automatically when files appear
- `linkedin_post_skill` - When LinkedIn posts approved
- Other skills based on file type

## Complete System Startup

### 1. Start Watchers (creates files)

```bash
cd ../../Automation/watchers
python3 run_all_watchers.py &
```

### 2. Start Orchestrator (processes files)

```bash
cd ../../Skills/integration_orchestrator
python3 index.py &
```

## Test the System

### Create Test File

```bash
echo "---
type: test
sender: Test User
timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
status: pending
---

This is a test message with keyword: invoice" > ../../Needs_Action/test_$(date +%s).md
```

### Watch Logs

```bash
tail -f ../../Logs/integration_orchestrator.log
```

Expected output:
```
[timestamp] [INFO] Routing event: needs_action_created for test_*.md
[timestamp] [INFO] Processing Needs_Action file: test_*.md
[timestamp] [INFO] Executing skill: process_needs_action
[timestamp] [INFO] Skill process_needs_action completed successfully
```

## Verify Processing

```bash
# Check if file moved to Done
ls -la ../../Done/

# Check if plan created
ls -la ../../Plans/

# Check if plan in Pending_Approval
ls -la ../../Pending_Approval/
```

## Stop Orchestrator

Press `Ctrl+C` in the terminal.

## Run as Background Service

```bash
# Using nohup
nohup python3 index.py > orchestrator.log 2>&1 &

# Using screen
screen -S orchestrator
python3 index.py
# Ctrl+A, D to detach
```

## Check Status

```bash
# Check if running
ps aux | grep index.py

# View recent logs
tail -20 ../../Logs/integration_orchestrator.log

# Check processed events
cat processed_events.json | python3 -m json.tool
```

## Troubleshooting

**No events detected:**
- Verify orchestrator is running
- Check file is `.md` format
- Check logs for errors

**Skills not executing:**
- Verify skill exists in `/Skills/`
- Check skill has executable file
- Review error in logs

**Duplicate processing:**
- Check `processed_events.json` is valid
- Clear state if needed: `echo "{}" > processed_events.json`

## Integration Flow

```
1. Watcher detects event (email/WhatsApp/LinkedIn)
   ↓
2. Watcher creates file in /Needs_Action
   ↓
3. Orchestrator detects new file
   ↓
4. Orchestrator triggers process_needs_action
   ↓
5. Plan created in /Pending_Approval
   ↓
6. Human reviews and approves
   ↓
7. Orchestrator detects approval
   ↓
8. Orchestrator triggers execution skill
   ↓
9. Action completed and logged
```

## Next Steps

1. **Configure watchers** - Set keywords and intervals
2. **Test workflow** - Send test messages
3. **Monitor logs** - Verify processing
4. **Optimize** - Adjust based on usage

---

For detailed documentation, see README.md
