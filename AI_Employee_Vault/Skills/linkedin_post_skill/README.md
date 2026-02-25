# LinkedIn Post Skill

Generates business posts using company tone from Company_Handbook.md and posts to LinkedIn with human approval workflow.

## Features

- **Company Tone Matching**: Reads Company_Handbook.md to match brand voice
- **Approval Workflow**: All posts require human approval before publishing
- **Draft Management**: Saves drafts to `/Pending_Approval` for review
- **Playwright Automation**: Browser automation for posting to LinkedIn
- **DRY_RUN Mode**: Test without actually posting
- **Session Persistence**: Maintains LinkedIn login across runs
- **Comprehensive Logging**: All actions logged to `/Logs`

## Installation

```bash
cd Skills/linkedin_post_skill
npm install
```

## First Run Setup

1. Run the skill to login to LinkedIn:
```bash
node index.js process
```

2. Browser will open - login to LinkedIn manually
3. Session will be saved in `linkedin_session/` directory
4. Future runs will use saved session automatically

## Usage

### Generate a Draft Post

```bash
# Basic generation
node index.js generate "New Product Launch"

# With key points
node index.js generate "Q1 Results" "Revenue up 25%" "New markets entered" "Team expanded"
```

This creates a draft in `/Pending_Approval/linkedin_draft_<timestamp>.md`

### Approve a Draft

1. Open the draft file in `/Pending_Approval/`
2. Review the content
3. Edit if needed
4. Change `status: pending_approval` to `status: approved`
5. Save the file

### Post Approved Drafts

```bash
node index.js process
```

This will:
- Find all approved drafts
- Post them to LinkedIn
- Archive to `/Posted/` directory

## Configuration

Edit `config.json`:

```json
{
  "dryRun": false,          // Set to true to test without posting
  "paths": {
    "handbookPath": "../../Company_Handbook.md"
  }
}
```

## Draft Format

```markdown
---
type: linkedin_post
status: pending_approval
created: 2026-02-23T10:30:00.000Z
topic: Product Launch
dry_run: false
---

📢 Excited to announce our new product launch!

1. Revolutionary features
2. Customer-focused design
3. Available now

What are your thoughts? Share in the comments below.

#Business #Leadership #Innovation

---
APPROVAL INSTRUCTIONS:
- Review the post above
- To approve: Change status to "approved" in the metadata
- To reject: Change status to "rejected" or delete this file
- To edit: Modify the post content directly
---
```

## DRY_RUN Mode

Test the entire workflow without actually posting:

1. Set `"dryRun": true` in `config.json`
2. Generate and approve drafts normally
3. Run `node index.js process`
4. Browser will open, content will be entered, but NOT submitted
5. Check logs to verify behavior

## File Structure

```
linkedin_post_skill/
├── index.js              # Main implementation
├── config.json           # Configuration
├── package.json          # Dependencies
├── skill.json           # Skill metadata
├── linkedin_session/    # Browser session (auto-generated)
└── README.md           # This file
```

## Workflow Example

```bash
# 1. Generate a draft
node index.js generate "Company Milestone" "10 years in business" "1000+ clients served"

# 2. Review and approve
# Edit /Pending_Approval/linkedin_draft_*.md
# Change status to "approved"

# 3. Post to LinkedIn
node index.js process
```

## Logs

All activity logged to: `/Logs/linkedin_post.log`

Example entries:
```
[2026-02-23T10:30:00.000Z] Company handbook loaded successfully
[2026-02-23T10:30:05.000Z] Generating post for topic: Product Launch
[2026-02-23T10:30:05.000Z] Draft created: linkedin_draft_1708684205000.md
[2026-02-23T10:35:00.000Z] Found 1 approved post(s)
[2026-02-23T10:35:10.000Z] Post submitted successfully!
```

## Troubleshooting

**Login required every time:**
- Session data may not be saving
- Check `linkedin_session/` directory permissions

**Post not appearing:**
- Check LinkedIn for rate limits
- Verify account has posting permissions
- Review logs for errors

**Company tone not applied:**
- Verify `Company_Handbook.md` exists at configured path
- Check logs for handbook loading errors

## Security Notes

- Session data contains authentication tokens
- Never commit `linkedin_session/` directory
- Review drafts before approval
- Use DRY_RUN mode for testing

## NPM Scripts

```bash
npm start          # Process approved posts
npm run generate   # Generate new draft
npm run post       # Process approved posts
```
