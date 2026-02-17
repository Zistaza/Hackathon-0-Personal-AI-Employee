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

#### 2.3 Create Execution Plan

**Action**: Create a detailed plan file in `/Plans` folder

**Filename Convention**: `PLAN_<original_filename>.md`

**Example**: If processing `customer-request.md`, create `PLAN_customer-request.md`

**Plan Format**:

```markdown
---
created: <ISO 8601 timestamp>
status: completed
source_file: <original filename>
---

## Objective

<Clear, concise summary of what needs to be accomplished - 2-3 sentences maximum>

## Steps

- [x] Step 1: <First action item>
- [x] Step 2: <Second action item>
- [x] Step 3: <Third action item>
- [x] Step 4: <Additional steps as needed>

## Notes

<Summary of reasoning, considerations, risks, and recommendations - 3-5 sentences>
```

**Requirements**:
- Use ISO 8601 timestamp format: `YYYY-MM-DDTHH:MM:SSZ`
- Status must be set to "completed" (analysis phase is complete)
- All steps should be marked with `[x]` (checkboxes checked)
- Objective should be clear and actionable
- Steps should be specific and sequential
- Notes should capture key reasoning and considerations

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

**Filename Convention**: Use current date in format `YYYY-MM-DD.json`

**Example**: `2026-02-18.json`

**Log Entry Format**:

```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "action_type": "process_file",
  "file": "<original filename>",
  "plan_created": "PLAN_<original filename>.md",
  "result": "success",
  "details": {
    "source_folder": "/Needs_Action",
    "destination_folder": "/Done",
    "plan_location": "/Pending_Approval",
    "analysis_summary": "<brief summary of what was analyzed>"
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

#### 2.7 Move Original File to Done

**Action**: Move the processed file from `/Needs_Action` to `/Done`

**Command**:
```bash
mv /Needs_Action/<filename>.md /Done/<filename>.md
```

**Validation**:
- Verify file exists in `/Done`
- Verify file no longer exists in `/Needs_Action`
- Preserve all file metadata and timestamps

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

### Scenario 2: Plan Creation Failure
**Symptom**: Cannot create plan file in `/Plans`
**Action**:
- Log error with details
- Do not move original file from `/Needs_Action`
- Retry once, then skip if still failing
- Flag for manual review

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

**v1.0** (2026-02-18)
- Initial implementation
- Core workflow: scan, analyze, plan, log, archive
- Safety rules: no deletions, idempotent behavior
- Error handling for common failure scenarios
