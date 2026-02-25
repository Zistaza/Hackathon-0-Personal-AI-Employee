---
title: Process Needs Action Skill
created_at: 2026-02-18T01:06:00Z
version: 1.0
tier: Bronze
skill_type: automated_workflow
---

# Process Needs Action Skill

## Purpose

Automatically process all files in the `/Needs_Action` folder by analyzing their content, creating structured execution plans, logging all actions, and archiving processed files.

## Skill Overview

This skill implements the core Bronze Tier workflow for processing action items. It ensures every file in `/Needs_Action` receives proper analysis, planning, logging, and archival without manual intervention.

---

## Execution Steps

### Step 1: Scan Needs_Action Folder

**Action**: List all markdown files in `/Needs_Action` folder

**Command**:
```bash
ls -1 /Needs_Action/*.md 2>/dev/null
```

**Validation**:
- If no files found, exit gracefully with message: "No files to process"
- If files found, proceed to Step 2

---

### Step 2: Process Each File

For each file found in `/Needs_Action`, execute the following sub-steps:

#### 2.1 Read File Contents

**Action**: Read the complete contents of the file

**Validation**:
- Verify file is readable
- Capture full content including frontmatter
- If file cannot be read, log error and skip to next file

#### 2.2 Analyze Intent

**Action**: Analyze the file content to understand:
- Primary objective or request
- Key requirements
- Constraints or dependencies
- Expected outcomes
- Complexity level

**Output**: Structured understanding of what needs to be accomplished

#### 2.3 Create Execution Plan (Enhanced)

**Action**: Create a detailed plan file in `/Plans` folder with comprehensive analysis

**Filename Convention**: `PLAN_<original_filename>.md`

**Example**: If processing `customer-request.md`, create `PLAN_customer-request.md`

**Enhanced Plan Format**:

```markdown
---
created: <ISO 8601 timestamp>
status: pending_review
source_file: <original filename>
priority: <low|medium|high|critical>
estimated_complexity: <simple|moderate|complex>
---

## Objective

<Clear, concise summary of what needs to be accomplished - 2-3 sentences maximum>

## Step-by-Step Checklist

- [ ] Step 1: <First action item with specific details>
- [ ] Step 2: <Second action item with specific details>
- [ ] Step 3: <Third action item with specific details>
- [ ] Step 4: <Additional steps as needed>
- [ ] Step 5: Verify completion and document results

**Success Criteria**:
- <Measurable outcome 1>
- <Measurable outcome 2>
- <Measurable outcome 3>

## Risk Analysis

### Identified Risks

**Technical Risks**:
- <Risk 1>: <Description and likelihood>
- <Risk 2>: <Description and likelihood>

**Business Risks**:
- <Risk 1>: <Description and impact>
- <Risk 2>: <Description and impact>

**Operational Risks**:
- <Risk 1>: <Description and mitigation>
- <Risk 2>: <Description and mitigation>

### Mitigation Strategies

1. **For <Risk Category>**: <Specific mitigation approach>
2. **For <Risk Category>**: <Specific mitigation approach>
3. **Contingency Plan**: <Fallback approach if primary plan fails>

### Risk Level Assessment

**Overall Risk**: <Low|Medium|High|Critical>

**Justification**: <1-2 sentences explaining the risk level>

## Approval Required

**Approval Status**: <Required|Not Required>

**Reason**: <Explanation of why approval is or isn't needed>

**If Approval Required**:

**Approver**: <Role or person who should approve>

**Approval Criteria**:
- [ ] Budget allocation confirmed (if applicable)
- [ ] Technical approach validated
- [ ] Timeline is acceptable
- [ ] Risk mitigation plan is adequate
- [ ] Resource availability confirmed

**Estimated Impact**:
- **Time**: <Estimated duration>
- **Resources**: <Required resources>
- **Cost**: <Estimated cost if applicable>
- **Dependencies**: <Any blocking dependencies>

**Approval Deadline**: <Date by which approval is needed>

**If Not Approved**: <Alternative action or escalation path>

## Implementation Notes

**Key Considerations**:
- <Important consideration 1>
- <Important consideration 2>
- <Important consideration 3>

**Dependencies**:
- <External dependency 1>
- <External dependency 2>

**Assumptions**:
- <Assumption 1>
- <Assumption 2>

**Recommendations**:
- <Recommendation 1>
- <Recommendation 2>
```

**Requirements**:
- Use ISO 8601 timestamp format: `YYYY-MM-DDTHH:MM:SSZ`
- Status must be set to "pending_review" (awaiting human review)
- All checklist items should be unchecked `[ ]` initially
- Objective should be clear, specific, and actionable
- Steps should be sequential and detailed enough to execute
- Risk analysis must identify at least 2-3 potential risks
- Approval section must evaluate if human approval is needed
- Success criteria must be measurable and specific

**Approval Decision Logic**:

Approval is **REQUIRED** if any of the following conditions are met:
- Financial impact exceeds defined threshold
- Changes affect production systems
- Involves customer-facing changes
- Requires access to sensitive data
- Has high or critical risk level
- Involves third-party integrations
- Requires resource allocation beyond normal capacity

Approval is **NOT REQUIRED** if:
- Internal documentation updates
- Low-risk routine tasks
- Pre-approved standard procedures
- Emergency fixes (with post-approval review)

**Validation Before File Creation**:
1. Verify `/Plans` directory exists (create if missing)
2. Check if plan file already exists (avoid overwriting)
3. Validate all required sections are populated
4. Ensure risk analysis has at least one risk identified
5. Confirm approval decision is justified

**Error Handling**:
- If plan creation fails, log detailed error
- Do NOT proceed to step 2.4 (copy to Pending_Approval)
- Do NOT proceed to step 2.7 (move to Done)
- Keep original file in `/Needs_Action` for retry
- Create error log entry with failure details

#### 2.4 Copy Plan to Pending_Approval

**Action**: Copy the created plan from `/Plans` to `/Pending_Approval`

**Command**:
```bash
cp /Plans/PLAN_<filename>.md /Pending_Approval/PLAN_<filename>.md
```

**Rationale**:
- `/Plans` serves as permanent archive of all plans created
- `/Pending_Approval` is the working folder for human review
- Original plan remains in `/Plans` for historical reference

**Validation**:
- Verify file exists in `/Pending_Approval`
- Verify file still exists in `/Plans` (archive copy)

#### 2.5 Update Dashboard

**Action**: Update `/Dashboard.md` with processing information

**Updates Required**:

1. **Recent Activity Section**: Add new entry at the top
   ```markdown
   **Latest Actions**: Processed <filename> - Plan created and moved to Pending_Approval
   ```

2. **Pending Approval Count**: Increment the count
   ```markdown
   **Current Count**: <new_count>
   ```

**Implementation**:
- Read current Dashboard.md
- Update Recent Activity with latest action
- Increment Pending Approval count
- Write updated content back to Dashboard.md

#### 2.6 Create JSON Log Entry (Enhanced)

**Action**: Write structured log entry to `/Logs/YYYY-MM-DD.json`

**Timing**: Execute AFTER successful plan creation, BEFORE moving file to Done

**Filename Convention**: Use current date in format `YYYY-MM-DD.json`

**Example**: `2026-02-18.json`

**Enhanced Log Entry Format**:

```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "action_type": "plan_created",
  "source_file": "<original filename>",
  "plan_file": "PLAN_<original filename>.md",
  "result": "success",
  "plan_metadata": {
    "priority": "<low|medium|high|critical>",
    "complexity": "<simple|moderate|complex>",
    "approval_required": "<true|false>",
    "risk_level": "<Low|Medium|High|Critical>",
    "objective_summary": "<brief one-line summary>"
  },
  "details": {
    "source_folder": "/Needs_Action",
    "plan_location": "/Plans",
    "pending_approval_location": "/Pending_Approval",
    "risks_identified": <number of risks>,
    "steps_count": <number of steps in checklist>
  }
}
```

**Safe Append Implementation**:

The logging system must handle these scenarios safely:
1. Log file doesn't exist (create new)
2. Log file is empty (treat as new)
3. Log file has corrupted JSON (backup and start fresh)
4. Write operation fails (preserve original, restore from backup)
5. Concurrent writes (use atomic operations)

**Bash Implementation** (Recommended):

```bash
#!/bin/bash

append_log_entry() {
    local log_file="$1"
    local new_entry="$2"
    local temp_file="${log_file}.tmp"
    local backup_file="${log_file}.backup"

    # Create logs directory if missing
    mkdir -p "$(dirname "$log_file")"

    # Check if log file exists and is valid
    if [ -f "$log_file" ]; then
        if jq empty "$log_file" 2>/dev/null; then
            existing_entries=$(cat "$log_file")
        else
            # Corrupted - backup and start fresh
            cp "$log_file" "${log_file}.corrupted.$(date +%s)"
            existing_entries="[]"
        fi
    else
        existing_entries="[]"
    fi

    # Append new entry
    echo "$existing_entries" | jq ". += [$new_entry]" > "$temp_file"

    # Verify and atomically replace
    if jq empty "$temp_file" 2>/dev/null; then
        [ -f "$log_file" ] && cp "$log_file" "$backup_file"
        mv "$temp_file" "$log_file"
        echo "✓ Log entry written"
        return 0
    else
        rm -f "$temp_file"
        return 1
    fi
}

# Usage
LOG_FILE="Logs/$(date +%Y-%m-%d).json"
NEW_ENTRY=$(cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "action_type": "process_file",
  "file": "example.md",
  "plan_created": "PLAN_example.md",
  "result": "success",
  "details": {
    "source_folder": "/Needs_Action",
    "destination_folder": "/Done",
    "plan_location": "/Pending_Approval",
    "analysis_summary": "Brief summary"
  }
}
EOF
)

append_log_entry "$LOG_FILE" "$NEW_ENTRY"
```

**Safety Features**:
- Atomic writes (temp file + rename)
- Automatic backup before modification
- Corrupted JSON detection and recovery
- Missing file handling
- Validation before replacing original

**Log File Structure**:
```json
[
  {
    "timestamp": "2026-02-18T01:15:00Z",
    "action_type": "process_file",
    "file": "customer-request.md",
    "plan_created": "PLAN_customer-request.md",
    "result": "success",
    "details": {
      "source_folder": "/Needs_Action",
      "destination_folder": "/Done",
      "plan_location": "/Pending_Approval",
      "analysis_summary": "Customer request for dashboard widget feature"
    }
  },
  {
    "timestamp": "2026-02-18T02:30:00Z",
    "action_type": "process_file",
    "file": "bug-report.md",
    "plan_created": "PLAN_bug-report.md",
    "result": "success",
    "details": {
      "source_folder": "/Needs_Action",
      "destination_folder": "/Done",
      "plan_location": "/Pending_Approval",
      "analysis_summary": "Bug fix for authentication timeout issue"
    }
  }
]
```

#### 2.7 Move Original File to Done (Enhanced)

**Action**: Move the processed file from `/Needs_Action` to `/Done`

**Critical Requirement**: This step MUST ONLY execute after:
1. ✓ Plan file successfully created in `/Plans`
2. ✓ Plan file successfully copied to `/Pending_Approval`
3. ✓ Log entry successfully written to `/Logs`

**Command**:
```bash
mv /Needs_Action/<filename>.md /Done/<filename>.md
```

**Pre-Move Validation Checklist**:
- [ ] Verify plan file exists: `/Plans/PLAN_<filename>.md`
- [ ] Verify plan copy exists: `/Pending_Approval/PLAN_<filename>.md`
- [ ] Verify log entry written: `/Logs/YYYY-MM-DD.json` contains entry
- [ ] Verify all required plan sections are populated
- [ ] Confirm no errors occurred in previous steps

**Post-Move Validation**:
- Verify file exists in `/Done`
- Verify file no longer exists in `/Needs_Action`
- Preserve all file metadata and timestamps

**Failure Handling**:
If ANY of the pre-move validations fail:
- DO NOT move the file
- Log detailed error with failed validation
- Keep file in `/Needs_Action` for retry
- Create error log entry
- Continue processing next file

**Rationale**:
This sequencing ensures that if plan creation fails, the original file remains in `/Needs_Action` for retry. This prevents data loss and maintains workflow integrity.

---

### Step 3: Final Dashboard Update

**Action**: Update Dashboard.md with final summary

**Updates Required**:

1. **Needs Action Count**: Set to 0 (all files processed)
   ```markdown
   **Current Count**: 0
   ```

2. **Recent Completions**: Update with summary
   ```markdown
   **Recent Completions**: Processed <N> files from Needs_Action
   ```

3. **Last Updated Timestamp**: Update to current time
   ```markdown
   **Last Updated**: <ISO 8601 timestamp>
   ```

---

## Safety Rules

### No File Deletions
- **NEVER** delete any files
- Only move files between folders
- Preserve all metadata and timestamps
- Maintain complete audit trail

### Idempotent Behavior
- Check if file already exists in `/Done` before processing
- Skip files that have already been processed
- Do not reprocess completed items
- Log skipped files for transparency

### Error Handling
- If a file cannot be read, log error and continue with next file
- If plan creation fails, log error and do not move original file
- If log write fails, continue processing but flag for manual review
- Never leave files in inconsistent state

### Validation Checks
- Verify all file operations complete successfully
- Confirm files exist in expected locations after moves
- Validate JSON log entries are well-formed
- Ensure Dashboard updates are accurate

---

## Expected Outcomes

After successful execution:

1. `/Needs_Action` folder is empty
2. All processed files are in `/Done` folder
3. All plans are in `/Pending_Approval` folder
4. Dashboard.md reflects current state
5. JSON log entries exist in `/Logs/YYYY-MM-DD.json`
6. No files have been deleted
7. All metadata is preserved

---

## Error Scenarios

### Scenario 1: File Read Failure
**Symptom**: Cannot read file in `/Needs_Action`
**Action**:
- Log error with filename and reason
- Skip to next file
- Do not move or modify the problematic file
- Flag for manual review

### Scenario 2: Plan Creation Failure (Enhanced)
**Symptom**: Cannot create plan file in `/Plans` or plan validation fails
**Action**:
- Log detailed error with specific failure reason:
  - Missing required sections
  - Invalid risk analysis
  - Approval decision not justified
  - File write permission issues
- Do NOT copy plan to `/Pending_Approval`
- Do NOT create log entry for successful processing
- Do NOT move original file from `/Needs_Action`
- Create error log entry with details
- Retry once with fresh analysis
- If retry fails, skip and flag for manual review
- Preserve original file in `/Needs_Action` for human intervention

**Error Log Entry Format**:
```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "action_type": "plan_creation_failed",
  "source_file": "<original filename>",
  "result": "error",
  "error_details": {
    "error_type": "<validation_failed|write_failed|analysis_failed>",
    "error_message": "<specific error description>",
    "retry_attempted": "<true|false>",
    "requires_manual_review": true
  }
}
```

### Scenario 3: Log Write Failure
**Symptom**: Cannot write to log file
**Action**:
- Continue processing (logging is important but not critical)
- Store log entry in temporary location
- Flag for manual log consolidation
- Do not halt workflow

### Scenario 4: Dashboard Update Failure
**Symptom**: Cannot update Dashboard.md
**Action**:
- Log error with details
- Continue processing other files
- Flag for manual dashboard update
- Ensure file movements still complete

---

## Usage

### Manual Invocation
```bash
# Run the skill manually
claude-code --skill process_needs_action
```

### Automated Invocation
- Can be triggered on schedule (e.g., every hour)
- Can be triggered by file system events (new file in /Needs_Action)
- Can be triggered by user command

### Verification
After execution, verify:
```bash
# Check Needs_Action is empty
ls -la /Needs_Action/

# Check Done folder has processed files
ls -la /Done/

# Check Pending_Approval has plans
ls -la /Pending_Approval/

# Check logs exist
ls -la /Logs/

# View Dashboard
cat Dashboard.md
```

---

## Performance Considerations

- Process files sequentially to maintain order
- Limit batch size to 10 files per execution for large queues
- Use efficient file operations (move, not copy+delete)
- Minimize Dashboard read/write operations
- Append to log files rather than rewriting

---

## Maintenance

### Regular Checks
- Verify log files are valid JSON
- Confirm Dashboard counts match actual folder contents
- Ensure no orphaned files in intermediate states
- Review error logs for patterns

### Cleanup
- Archive old log files by month/year if needed
- Compress Done folder if it grows large
- Maintain referential integrity of all links

---

## Version History

**v2.0** (2026-02-23)
- Enhanced plan creation with comprehensive structure
- Added Risk Analysis section with technical, business, and operational risks
- Added Approval Required section with decision logic and criteria
- Added Step-by-Step Checklist with success criteria
- Enhanced metadata: priority, complexity, risk level
- Updated workflow sequencing: plan creation MUST succeed before file movement
- Enhanced error handling for plan validation failures
- Updated JSON logging to include plan metadata
- Added pre-move validation checklist
- Improved error scenarios with detailed recovery procedures

**v1.0** (2026-02-18)
- Initial implementation
- Core workflow: scan, analyze, plan, log, archive
- Safety rules: no deletions, idempotent behavior
- Error handling for common failure scenarios
