#!/bin/bash
#
# Safe JSON Log Appender for Bronze Tier AI Employee
# Usage: ./append_log.sh <log_file> <json_entry>
#

set -euo pipefail

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
            # Valid JSON - read existing entries
            existing_entries=$(cat "$log_file")
        else
            # Corrupted JSON - backup and start fresh
            echo "⚠ Warning: Corrupted log file detected, creating backup..."
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
        echo "✗ Error: Failed to create valid JSON"
        rm -f "$temp_file"
        return 1
    fi
}

# Main execution
if [ $# -lt 2 ]; then
    echo "Usage: $0 <log_file> <json_entry>"
    echo ""
    echo "Example:"
    echo "  $0 Logs/2026-02-18.json '{\"timestamp\":\"2026-02-18T10:00:00Z\",\"action\":\"test\"}'"
    exit 1
fi

LOG_FILE="$1"
NEW_ENTRY="$2"

# Validate that new_entry is valid JSON
if ! echo "$NEW_ENTRY" | jq empty 2>/dev/null; then
    echo "✗ Error: Invalid JSON entry provided"
    exit 1
fi

# Append the log entry
append_log_entry "$LOG_FILE" "$NEW_ENTRY"
