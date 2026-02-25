# Email Approval Workflow - Quick Reference

## Quick Start

### 1. Start the Enhanced Orchestrator

```bash
cd Skills/integration_orchestrator
python3 index.py
```

### 2. Create an Email Approval Request

```bash
python3 create_email_approval.py \
  "recipient@example.com" \
  "Email Subject" \
  "Email body content here"
```

### 3. Approve or Reject

**To Approve:**
```bash
mv ../../Pending_Approval/email/email_approval_*.md ../../Approved/
```

**To Reject:**
```bash
mv ../../Pending_Approval/email/email_approval_*.md ../../Rejected/
```

### 4. Monitor Results

```bash
# Watch orchestrator logs
tail -f ../../Logs/integration_orchestrator.log

# Check email logs
cat ../../Logs/$(date +%Y-%m-%d).json

# View sent emails
ls -la ../../Done/
```

## Directory Structure

```
AI_Employee_Vault/
├── Pending_Approval/email/  ← Approval requests wait here
├── Approved/                ← Move here to SEND email
├── Rejected/                ← Move here to CANCEL email
├── Done/                    ← Sent emails archived here
└── Logs/
    ├── integration_orchestrator.log
    └── YYYY-MM-DD.json      ← Daily email action logs
```

## Workflow Summary

```
1. Create Request → /Pending_Approval/email/
2. Human Reviews
3. Move to /Approved/ OR /Rejected/
4. Orchestrator Detects Move
5. Send Email (if approved) OR Log Rejection
6. Archive to /Done/
```

## Key Features

✓ **No Automatic Sending** - Every email requires human approval
✓ **Duplicate Prevention** - Same email won't be sent twice
✓ **Complete Logging** - All actions logged to daily JSON files
✓ **Audit Trail** - All approvals archived in /Done/
✓ **Simple Workflow** - Just move files between folders

## Testing

```bash
# Run test workflow
python3 test_email_workflow.py

# Check status
python3 test_email_workflow.py status
```

## Troubleshooting

**Email not sending?**
```bash
# Check orchestrator is running
ps aux | grep "python3 index.py"

# Check logs
tail -f ../../Logs/integration_orchestrator.log

# Verify SMTP config
cat ../../mcp_servers/email_mcp/.env
```

**File not detected?**
- Ensure file is .md format
- Use `mv` not `cp` to move files
- Check orchestrator is watching the directory

## Integration Example

```python
# In your skill code
from create_email_approval import create_email_approval

# Create approval request instead of sending directly
create_email_approval(
    to="client@example.com",
    subject="Project Update",
    body="The project is on track."
)
```

## State Files

- `processed_events.json` - Tracks all orchestrator events
- `processed_approvals.json` - Prevents duplicate email sending

## Commands Cheat Sheet

```bash
# Create approval
python3 create_email_approval.py "to@email.com" "Subject" "Body"

# Approve
mv ../../Pending_Approval/email/FILE.md ../../Approved/

# Reject
mv ../../Pending_Approval/email/FILE.md ../../Rejected/

# View logs
tail -f ../../Logs/integration_orchestrator.log

# Check status
python3 test_email_workflow.py status

# List pending approvals
ls -la ../../Pending_Approval/email/

# List sent emails
ls -la ../../Done/
```

---

For detailed documentation, see: `EMAIL_APPROVAL_WORKFLOW.md`
