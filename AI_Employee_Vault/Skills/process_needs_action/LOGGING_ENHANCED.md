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

```python
import json
import shutil
from pathlib import Path
from datetime import datetime

def append_log_entry(log_entry, logs_dir="/Logs"):
    """
    Safely append a log entry to the daily JSON log file.
    Handles missing files, corrupted JSON, and atomic writes.
    """
    # Determine log file path
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = Path(logs_dir) / f"{today}.json"
    temp_file = Path(logs_dir) / f"{today}.json.tmp"
    backup_file = Path(logs_dir) / f"{today}.json.backup"

    try:
        # Step 1: Read existing log entries
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                    # Handle empty file
                    if not content:
                        log_entries = []
                    else:
                        log_entries = json.loads(content)

                        # Ensure it's a list
                        if not isinstance(log_entries, list):
                            raise ValueError("Log file is not a JSON array")

            except (json.JSONDecodeError, ValueError) as e:
                # Corrupted JSON - create backup and start fresh
                print(f"Warning: Corrupted log file detected: {e}")

                # Create backup of corrupted file
                if log_file.exists():
                    backup_path = Path(logs_dir) / f"{today}.json.corrupted.{int(datetime.now().timestamp())}"
                    shutil.copy2(log_file, backup_path)
                    print(f"Backup created: {backup_path}")

                # Start with empty array
                log_entries = []
        else:
            # File doesn't exist - start fresh
            log_entries = []

        # Step 2: Append new entry
        log_entries.append(log_entry)

        # Step 3: Write to temporary file (atomic write)
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(log_entries, f, indent=2, ensure_ascii=False)

        # Step 4: Create backup of existing file (if it exists)
        if log_file.exists():
            shutil.copy2(log_file, backup_file)

        # Step 5: Atomically replace old file with new file
        shutil.move(str(temp_file), str(log_file))

        # Step 6: Clean up backup (optional - keep for safety)
        # if backup_file.exists():
        #     backup_file.unlink()

        print(f"✓ Log entry written to {log_file}")
        return True

    except Exception as e:
        print(f"Error writing log entry: {e}")

        # Clean up temp file if it exists
        if temp_file.exists():
            temp_file.unlink()

        # Try to restore from backup if write failed
        if backup_file.exists() and not log_file.exists():
            shutil.copy2(backup_file, log_file)
            print("Restored log file from backup")

        return False
```

**Usage Example**:

```python
# Create log entry
log_entry = {
    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
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
}

# Safely append to log
append_log_entry(log_entry, logs_dir="/Logs")
```

**Bash Implementation** (Alternative):

For environments without Python, use this bash approach:

```bash
#!/bin/bash

# Function to safely append log entry
append_log_entry() {
    local log_file="$1"
    local new_entry="$2"
    local temp_file="${log_file}.tmp"
    local backup_file="${log_file}.backup"

    # Create logs directory if missing
    mkdir -p "$(dirname "$log_file")"

    # Check if log file exists
    if [ -f "$log_file" ]; then
        # Validate existing JSON
        if jq empty "$log_file" 2>/dev/null; then
            # Valid JSON - read existing entries
            existing_entries=$(cat "$log_file")
        else
            # Corrupted JSON - create backup and start fresh
            echo "Warning: Corrupted log file detected"
            cp "$log_file" "${log_file}.corrupted.$(date +%s)"
            existing_entries="[]"
        fi
    else
        # File doesn't exist - start with empty array
        existing_entries="[]"
    fi

    # Append new entry to array
    echo "$existing_entries" | jq ". += [$new_entry]" > "$temp_file"

    # Verify new file is valid JSON
    if jq empty "$temp_file" 2>/dev/null; then
        # Create backup of existing file
        [ -f "$log_file" ] && cp "$log_file" "$backup_file"

        # Atomically replace old file
        mv "$temp_file" "$log_file"

        echo "✓ Log entry written to $log_file"
        return 0
    else
        echo "Error: Failed to create valid JSON"
        rm -f "$temp_file"
        return 1
    fi
}

# Usage example
LOG_FILE="Logs/$(date +%Y-%m-%d).json"
NEW_ENTRY=$(cat <<'EOF'
{
  "timestamp": "2026-02-18T02:30:00Z",
  "action_type": "process_file",
  "file": "customer-request.md",
  "plan_created": "PLAN_customer-request.md",
  "result": "success",
  "details": {
    "source_folder": "/Needs_Action",
    "destination_folder": "/Done",
    "plan_location": "/Pending_Approval",
    "analysis_summary": "Customer request for dashboard widget"
  }
}
EOF
)

append_log_entry "$LOG_FILE" "$NEW_ENTRY"
```

**Safety Features**:

1. **Atomic Writes**: Write to temporary file first, then rename (prevents corruption if interrupted)

2. **Backup Creation**: Creates backup before modifying existing file

3. **Corruption Handling**: Detects corrupted JSON and creates timestamped backup

4. **Missing File Handling**: Creates new log file with proper JSON array format

5. **Validation**: Verifies JSON is valid before replacing original file

6. **Error Recovery**: Restores from backup if write operation fails

7. **UTF-8 Support**: Handles international characters properly

**Error Scenarios**:

| Scenario | Handling |
|----------|----------|
| Log file doesn't exist | Create new file with JSON array containing single entry |
| Log file is empty | Treat as new file, create JSON array |
| Log file has corrupted JSON | Create timestamped backup, start fresh with new entry |
| Write operation fails | Keep original file, clean up temp file, restore from backup if needed |
| Disk full | Fail gracefully, preserve original file |
| Permission denied | Log error, continue processing (logging is non-critical) |

**Verification**:

After writing, verify the log file:

```bash
# Check if file is valid JSON
jq empty Logs/2026-02-18.json && echo "✓ Valid JSON" || echo "✗ Invalid JSON"

# Pretty print the log
jq . Logs/2026-02-18.json

# Count entries
jq 'length' Logs/2026-02-18.json

# Get last entry
jq '.[-1]' Logs/2026-02-18.json
```

**Log File Structure** (After Multiple Entries):

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

**Performance Considerations**:

- For files with < 1000 entries: Read entire file, append, write back (fast)
- For files with > 1000 entries: Consider rotating to new file or archiving old entries
- Backup files can be cleaned up after successful write (or kept for audit trail)
- Use `.backup` extension for easy identification and cleanup

**Maintenance**:

```bash
# Clean up old backup files (older than 7 days)
find Logs -name "*.backup" -mtime +7 -delete

# Clean up corrupted file backups (older than 30 days)
find Logs -name "*.corrupted.*" -mtime +30 -delete

# Archive logs older than 90 days
find Logs -name "*.json" -mtime +90 -exec gzip {} \;
```
