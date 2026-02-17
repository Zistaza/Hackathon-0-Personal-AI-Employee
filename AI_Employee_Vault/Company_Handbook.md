---
title: Company Handbook
created_at: 2026-02-18T01:06:00Z
version: 1.0
tier: Bronze
---

# Mission

To establish a reliable, scalable knowledge management system that enables AI agents to operate autonomously while maintaining organizational standards and workflow integrity.

# Operating Principles

1. **Clarity Over Complexity** - Documentation should be concise, actionable, and immediately understandable
2. **Consistency in Execution** - All agents follow standardized workflows and file handling procedures
3. **Transparency** - All actions, decisions, and status changes are documented and visible
4. **Safety First** - Never auto-delete files or perform irreversible actions without explicit approval
5. **Accountability** - Every task has clear ownership and completion criteria

---

# Communication Rules

## Professional Standards
- Use clear, concise, professional language
- Provide context for all decisions and recommendations
- Flag uncertainties and ambiguities explicitly
- Update dashboards after significant actions
- Document all reasoning in logs

## Status Updates
- Update file metadata when status changes
- Log all file movements between folders
- Maintain audit trail of all actions
- Report completion status accurately

## Escalation Protocol
- Escalate blockers or ambiguities to human oversight
- Request approval for irreversible actions
- Seek clarification when requirements are unclear
- Never assume or guess critical information

---

# Processing Rules

## Core Workflow: Needs_Action Processing

Every file in `/Needs_Action` **MUST** follow this mandatory sequence:

### 1. Analysis Phase
- Read and understand the complete request
- Identify requirements, constraints, and success criteria
- Research relevant context and dependencies
- Document findings and considerations

### 2. Plan Creation Phase
- Create a detailed execution plan in `/Plans` folder
- Include step-by-step actions
- Identify risks and mitigation strategies
- Specify required resources and dependencies
- Move plan to `/Pending_Approval` for human review

### 3. Logging Phase
- Create a JSON log entry in `/Logs` folder
- Document analysis, plan creation, and status
- Include timestamps and file references
- Maintain complete audit trail

### 4. Completion Phase
- Move original file from `/Needs_Action` to `/Done`
- Update Dashboard with completion status
- Ensure all references and links remain valid

## File Safety Rules

### Never Auto-Delete
- **NEVER** automatically delete any files
- Files may only be moved between workflow folders
- Maintain complete history in `/Done` folder
- Preserve all metadata and timestamps

### Never Perform Irreversible Actions
- Request approval for destructive operations
- Create backups before major modifications
- Document all changes in logs
- Provide rollback procedures when applicable

---

# File Handling Policy

## File Creation
- All new files must include YAML frontmatter with: `title`, `created_at`, `status`
- Use descriptive, kebab-case filenames (e.g., `project-proposal.md`)
- Place files in appropriate workflow folders based on current status

## File Modification
- Update `modified_at` timestamp in frontmatter when making changes
- Preserve original creation metadata
- Document significant changes in file history or logs

## File Movement
- Files progress through workflow stages systematically
- Update status field in frontmatter when moving files
- Log all movements in `/Logs` folder
- Maintain referential integrity for internal links

---

# Workflow Definitions

## /Inbox
**Purpose**: Entry point for all new items requiring processing

**Agent Actions**:
- Review and categorize new items
- Add necessary metadata
- Move to `/Needs_Action` with clear next steps

## /Needs_Action
**Purpose**: Active work queue for items requiring analysis and planning

**Agent Actions**:
- Analyze each item thoroughly
- Create execution plan
- Log all actions
- Move to `/Done` after processing

## /Plans
**Purpose**: Permanent archive of all generated execution plans

**Agent Actions**:
- Create detailed, actionable plans
- Include all necessary context
- Copy to `/Pending_Approval` for review
- Maintain original in `/Plans` as historical record

## /Pending_Approval
**Purpose**: Plans awaiting human review and decision

**Agent Actions**:
- Wait for human approval/rejection
- Do not execute until approved
- Move to `/Approved` or `/Rejected` based on decision

## /Approved
**Purpose**: Plans approved for execution

**Agent Actions**:
- Execute approved plans
- Document execution progress
- Move to `/Done` upon completion

## /Rejected
**Purpose**: Plans rejected with feedback

**Agent Actions**:
- Review rejection feedback
- Revise and resubmit if requested
- Archive for learning purposes

## /Done
**Purpose**: Archive of completed work

**Agent Actions**:
- Verify completion criteria met
- Ensure documentation is complete
- Maintain for historical reference

## /Logs
**Purpose**: System activity and audit trail

**Agent Actions**:
- Create JSON log entries for all significant actions
- Maintain chronological record
- Enable traceability and debugging

---

# Dashboard Update Policy

## Update Frequency
- After processing each item
- Upon completion of any task
- When system status changes
- Minimum once per operational session

## Required Updates
- Task counts for each workflow stage
- Status indicators
- Recent activity summary
- Pending items requiring attention
