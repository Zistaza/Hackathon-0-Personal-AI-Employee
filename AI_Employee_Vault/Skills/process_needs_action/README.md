# Process Needs Action Skill v2.0

Automatically processes files in `/Needs_Action` with comprehensive planning, risk analysis, and approval workflows.

## Quick Start

```bash
cd Skills/process_needs_action
./run.sh
```

## What's New in v2.0

### Enhanced Planning
- **Risk Analysis**: Identifies technical, business, and operational risks
- **Approval Workflow**: Determines if human approval is required
- **Success Criteria**: Measurable outcomes for each plan
- **Priority & Complexity**: Metadata for better resource planning

### Improved Safety
- **Strict Sequencing**: Files only move to /Done after successful plan creation
- **Pre-Move Validation**: Verifies all prerequisites before file movement
- **Enhanced Logging**: Tracks plan metadata and characteristics
- **Error Recovery**: Files remain in /Needs_Action on failure for retry

## How It Works

### Workflow

1. **Scan** `/Needs_Action` for markdown files
2. **Analyze** content and extract metadata
3. **Generate** comprehensive plan with risk analysis
4. **Validate** plan meets all requirements
5. **Copy** plan to `/Pending_Approval` for review
6. **Log** plan creation with metadata
7. **Move** original file to `/Done` (only if all above succeed)

### Plan Structure

Each generated plan includes:

```markdown
---
created: 2026-02-23T03:15:00Z
status: pending_review
source_file: original_file.md
priority: high|medium|low|critical
estimated_complexity: simple|moderate|complex
---

## Objective
Clear summary of what needs to be accomplished

## Step-by-Step Checklist
- [ ] Detailed action items
- [ ] With success criteria

## Risk Analysis
### Identified Risks
- Technical, Business, and Operational risks
### Mitigation Strategies
- Specific approaches for each risk
### Risk Level Assessment
- Overall risk rating with justification

## Approval Required
- Decision: Required or Not Required
- Justification and criteria
- Approval deadline and impact

## Implementation Notes
- Key considerations
- Dependencies and assumptions
- Recommendations
```

## Usage

### Manual Execution

```bash
# Run the skill
./run.sh

# Or directly with Python
python3 process_needs_action.py
```

### Automated Execution

Add to crontab for scheduled processing:

```bash
# Run every hour
0 * * * * cd /path/to/Skills/process_needs_action && ./run.sh

# Run every 30 minutes
*/30 * * * * cd /path/to/Skills/process_needs_action && ./run.sh
```

### Verification

After execution, verify:

```bash
# Check Needs_Action is empty (or has only unprocessed files)
ls -la ../../Needs_Action/

# Check Plans directory has new plans
ls -la ../../Plans/

# Check Pending_Approval has plans ready for review
ls -la ../../Pending_Approval/

# Check Done has processed files
ls -la ../../Done/

# View logs
cat ../../Logs/process_needs_action.log
cat ../../Logs/$(date +%Y-%m-%d).json
```

## Approval Workflow

### When Approval is Required

Approval is **REQUIRED** if:
- Financial impact exceeds threshold
- Production system changes
- Customer-facing changes
- Sensitive data access
- High/critical risk level
- Third-party integrations
- Resource allocation beyond capacity

### When Approval is NOT Required

Approval is **NOT REQUIRED** if:
- Internal documentation updates
- Low-risk routine tasks
- Pre-approved standard procedures
- Emergency fixes (with post-approval review)

### Reviewing Plans

1. Open plan file in `/Pending_Approval/`
2. Review objective, steps, and risks
3. Validate approval decision
4. Check success criteria are measurable
5. Approve or reject based on criteria

## File Locations

```
AI_Employee_Vault/
├── Needs_Action/          # Input: Files to process
├── Plans/                 # Archive: All generated plans
├── Pending_Approval/      # Working: Plans awaiting review
├── Done/                  # Archive: Processed files
└── Logs/                  # Logs: Daily JSON logs + skill log
```

## Examples

### Input File

`/Needs_Action/whatsapp_1708656000000.md`:
```markdown
---
type: whatsapp
sender: John Doe
timestamp: 2026-02-23T10:30:45.123Z
status: pending
---

Please send the invoice for last month urgently.
```

### Generated Plan

`/Plans/PLAN_whatsapp_1708656000000.md`:
- Priority: high (contains "urgently")
- Complexity: moderate
- Approval Required: Yes (financial transaction)
- Risk Level: Medium
- 5-step checklist with success criteria
- 3 risk categories identified
- Mitigation strategies provided

### Log Entry

`/Logs/2026-02-23.json`:
```json
{
  "timestamp": "2026-02-23T03:15:00Z",
  "action_type": "plan_created",
  "source_file": "whatsapp_1708656000000.md",
  "plan_file": "PLAN_whatsapp_1708656000000.md",
  "result": "success",
  "plan_metadata": {
    "priority": "high",
    "complexity": "moderate",
    "approval_required": true,
    "risk_level": "Medium"
  }
}
```

## Error Handling

### Plan Creation Fails

**Behavior**: File remains in `/Needs_Action`

**Reason**: Ensures retry capability and prevents data loss

**Recovery**: Fix issue and re-run skill

### Validation Fails

**Behavior**: File remains in `/Needs_Action`

**Logged**: Error details in logs

**Recovery**: Review logs, fix issue, retry

### Partial Success

**Behavior**: Only completed steps are preserved

**Example**: If plan created but copy fails, plan exists in `/Plans` but file stays in `/Needs_Action`

**Recovery**: Next run will skip existing plan and retry copy

## Troubleshooting

### No files processed

**Check**:
- Files exist in `/Needs_Action/`
- Files have `.md` extension
- Files are readable

### Plans not created

**Check**:
- `/Plans/` directory exists and is writable
- Python 3 is installed
- No permission issues

### Files not moving to Done

**Check**:
- Plan creation succeeded
- Plan copied to Pending_Approval
- Log entry created
- All prerequisites validated

### Review logs

```bash
# Skill execution log
tail -f ../../Logs/process_needs_action.log

# Daily JSON log
cat ../../Logs/$(date +%Y-%m-%d).json | jq .
```

## Configuration

### Customizing Analysis

Edit `process_needs_action.py`:

```python
# Adjust priority keywords
if any(word in content_lower for word in ["urgent", "critical", "asap"]):
    analysis["priority"] = "high"

# Adjust approval thresholds
if any(word in content_lower for word in ["payment", "invoice"]):
    analysis["approval_required"] = True
```

### Customizing Plan Template

Edit the `create_plan()` method in `process_needs_action.py` to modify:
- Plan structure
- Risk categories
- Success criteria format
- Implementation notes

## Files

- `SKILL.md` - Complete skill documentation (v2.0)
- `process_needs_action.py` - Python implementation
- `run.sh` - Bash runner script
- `EXAMPLE_PLAN.md` - Complete example plan
- `ENHANCEMENT_SUMMARY.md` - v2.0 changes overview
- `ENHANCED_PLAN_SECTION.md` - Plan format reference
- `append_log.py` - JSON logging utility
- `append_log.sh` - Bash logging script

## Version History

**v2.0** (2026-02-23)
- Enhanced plan structure with risk analysis
- Approval workflow with decision logic
- Strict sequencing with validation
- Enhanced metadata and logging
- Python implementation

**v1.0** (2026-02-18)
- Initial implementation
- Basic workflow
- Simple plan format

## Support

For issues or questions:
1. Review logs in `/Logs/`
2. Check `SKILL.md` for detailed documentation
3. Examine `EXAMPLE_PLAN.md` for reference
4. Review `ENHANCEMENT_SUMMARY.md` for v2.0 changes

---

**Status**: Production Ready
**Version**: 2.0
**Last Updated**: 2026-02-23
