---
title: LinkedIn Post Skill
created_at: 2026-02-23T02:49:00Z
version: 1.0
tier: Silver
skill_type: content_automation
---

# LinkedIn Post Skill

## Purpose

Generates business posts using company tone from Company_Handbook.md and posts to LinkedIn with human approval workflow.

## Skill Overview

This skill automates LinkedIn content creation and posting while maintaining brand voice consistency and requiring human approval before publication. It uses Playwright browser automation for posting and implements a draft-approval-publish workflow.

---

## Features

- **Company Tone Matching**: Reads Company_Handbook.md to match brand voice
- **Approval Workflow**: All posts require human approval before publishing
- **Draft Management**: Saves drafts to `/Pending_Approval` for review
- **Playwright Automation**: Browser automation for posting to LinkedIn
- **DRY_RUN Mode**: Test without actually posting
- **Session Persistence**: Maintains LinkedIn login across runs
- **Comprehensive Logging**: All actions logged to `/Logs`

---

## Configuration

Edit `config.json` to customize:

```json
{
  "paths": {
    "handbookPath": "../../Company_Handbook.md",
    "pendingApprovalDir": "../../Pending_Approval",
    "postedDir": "../../Posted",
    "logsDir": "../../Logs",
    "userDataDir": "./linkedin_session"
  },
  "browser": {
    "headless": false,
    "viewport": {
      "width": 1280,
      "height": 720
    }
  },
  "dryRun": false
}
```

---

## Execution Steps

### Mode 1: Generate Draft

#### Step 1: Load Company Handbook

**Action**: Read Company_Handbook.md to understand brand voice

**Purpose**: Ensure generated content matches company tone

**Fallback**: If handbook not found, use generic professional tone

#### Step 2: Generate Post Content

**Action**: Create post based on topic and key points

**Input Parameters**:
- Topic: Main subject of the post
- Key Points: Array of bullet points to include

**Content Structure**:
```
📢 [Topic]

1. [Key Point 1]
2. [Key Point 2]
3. [Key Point 3]

[Call to action]

#Hashtags
```

#### Step 3: Create Draft File

**Action**: Save draft to `/Pending_Approval`

**Filename**: `linkedin_draft_<timestamp>.md`

**Format**:
```markdown
---
type: linkedin_post
status: pending_approval
created: <ISO 8601 timestamp>
topic: <topic>
dry_run: <true|false>
---

[Post content]

---
APPROVAL INSTRUCTIONS:
- Review the post above
- To approve: Change status to "approved" in the metadata
- To reject: Change status to "rejected" or delete this file
- To edit: Modify the post content directly
---
```

#### Step 4: Log Draft Creation

**Action**: Append to `/Logs/linkedin_post.log`

**Log Entry**:
```
[timestamp] Draft created: linkedin_draft_<timestamp>.md
```

---

### Mode 2: Process Approved Posts

#### Step 1: Scan Pending Approval Directory

**Action**: Find all markdown files in `/Pending_Approval`

**Filter**: Only files with `status: approved` in frontmatter

**Output**: Array of approved draft objects

#### Step 2: Initialize Browser Session

**Action**: Launch Chromium with persistent context

**Details**:
- Uses saved session from `linkedin_session/` directory
- Opens LinkedIn in non-headless mode
- Maintains login across runs

**First Run**:
- Login form will appear
- User logs in manually
- Session saved automatically

#### Step 3: Navigate to LinkedIn

**Action**: Load https://www.linkedin.com

**Validation**:
- Wait for either login form or feed
- If login form: wait for user to login (up to 5 minutes)
- If feed: already logged in

#### Step 4: Open Post Composer

**Action**: Click "Start a post" button

**Selectors Used**:
- `[data-test-id="share-box-open"]` - Share box trigger
- `.share-box-feed-entry__trigger` - Alternative selector

**Wait**: 1.5 seconds for composer to appear

#### Step 5: Enter Post Content

**Action**: Type post content into editor

**Selectors Used**:
- `.ql-editor` - Post editor
- `[data-placeholder="What do you want to talk about?"]` - Alternative

**Process**:
1. Click editor to focus
2. Type content line by line
3. Press Enter between lines to preserve formatting

#### Step 6: Submit or Preview (Based on DRY_RUN)

**If DRY_RUN = false**:
- Click Post button
- Wait 3 seconds for submission
- Log success

**If DRY_RUN = true**:
- Wait 2 seconds (preview)
- Close composer without posting
- Log dry run completion

**Selectors Used**:
- `[data-test-id="share-box-post-button"]` - Post button
- `button[aria-label*="Post"]` - Alternative selector

#### Step 7: Archive Posted Draft

**Action**: Move draft from `/Pending_Approval` to `/Posted`

**Filename**: `posted_<timestamp>_<original_filename>`

**Purpose**: Maintain history of published posts

#### Step 8: Log Posting Activity

**Action**: Append to `/Logs/linkedin_post.log`

**Log Entries**:
- Post submitted successfully (or dry run completed)
- Draft archived

#### Step 9: Process Next Approved Post

**Action**: Repeat steps 4-8 for each approved draft

**Wait**: 5 seconds between posts to avoid rate limiting

#### Step 10: Close Browser

**Action**: Close browser context

**Note**: Session data is preserved in `linkedin_session/`

---

## Approval Workflow

### Creating a Draft

```bash
node index.js generate "Product Launch" "New features" "Available now"
```

**Result**: Draft created in `/Pending_Approval/linkedin_draft_<timestamp>.md`

### Reviewing a Draft

1. Open draft file in `/Pending_Approval/`
2. Review content for accuracy and tone
3. Edit content if needed
4. Change `status: pending_approval` to `status: approved`
5. Save file

### Publishing Approved Drafts

```bash
node index.js process
```

**Result**: All approved drafts posted to LinkedIn and archived

---

## Safety Rules

### Session Security
- Never commit `linkedin_session/` directory
- Contains authentication tokens
- Add to `.gitignore`

### Content Review
- All posts require human approval
- No automatic posting without approval
- Drafts can be edited before approval

### DRY_RUN Mode
- Test workflow without posting
- Set `"dryRun": true` in config.json
- Content entered but not submitted

### Rate Limiting
- 5-second delay between posts
- Prevents LinkedIn rate limiting
- Maintains account health

---

## Expected Outcomes

### After Generate Mode:

1. Draft file created in `/Pending_Approval`
2. Content matches company tone (if handbook available)
3. Metadata includes topic and timestamp
4. Activity logged

### After Process Mode:

1. All approved drafts posted to LinkedIn
2. Drafts archived to `/Posted`
3. Browser session maintained
4. Activity logged
5. No unapproved drafts posted

---

## Error Scenarios

### Scenario 1: Company Handbook Not Found
**Symptom**: Cannot read Company_Handbook.md
**Action**: Use generic professional tone, log warning

### Scenario 2: Login Required
**Symptom**: LinkedIn session expired
**Action**: Wait for user to login, save new session

### Scenario 3: Post Composer Not Found
**Symptom**: Selectors don't match elements
**Action**: Log error, skip post, continue with next

### Scenario 4: Rate Limiting
**Symptom**: LinkedIn blocks posting
**Action**: Log error, stop processing, retry later

### Scenario 5: No Approved Drafts
**Symptom**: No files with status: approved
**Action**: Log "No approved posts found", exit gracefully

---

## Usage

### Generate a Draft

```bash
# Basic generation
node index.js generate "New Product Launch"

# With key points
node index.js generate "Q1 Results" "Revenue up 25%" "New markets" "Team growth"
```

### Approve a Draft

```bash
# Edit the draft file
vim ../../Pending_Approval/linkedin_draft_<timestamp>.md

# Change status to approved
status: approved
```

### Post Approved Drafts

```bash
# Process all approved drafts
node index.js process

# Or use the runner script
./run.sh
```

### Test with DRY_RUN

```bash
# Edit config.json
"dryRun": true

# Process drafts (won't actually post)
node index.js process
```

---

## Performance Considerations

- Processes one post at a time
- 5-second delay between posts
- Maintains persistent session (no re-login)
- Efficient selector usage
- Minimal browser overhead

---

## Maintenance

### Regular Checks
- Verify session is still valid
- Check log file for errors
- Confirm posts are being published
- Review archived posts in `/Posted`

### Cleanup
- Archive old logs monthly
- Review `/Posted` directory periodically
- Update LinkedIn selectors if UI changes

### Session Management
- Re-login if session expires
- Clear `linkedin_session/` to force re-login
- Monitor for LinkedIn security alerts

---

## Integration

### With process_needs_action Skill
- Can be triggered by action items
- Plans can include "Create LinkedIn post" steps
- Approval workflow integrates with existing processes

### Workflow Example
1. Marketing team creates content brief
2. Brief placed in `/Needs_Action`
3. process_needs_action creates plan
4. Plan includes "Generate LinkedIn post" step
5. LinkedIn post skill generates draft
6. Marketing reviews and approves
7. Post published automatically

---

## Version History

**v1.0** (2026-02-23)
- Initial implementation
- Playwright browser automation
- Draft-approval-publish workflow
- Company tone matching
- DRY_RUN mode
- Session persistence
- Comprehensive logging
