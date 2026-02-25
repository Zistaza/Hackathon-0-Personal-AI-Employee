# Email MCP Server

Production-ready Email MCP Server for Claude Code Router with enterprise-grade features.

## Features

- **Send Email**: Send emails via SMTP with full validation
- **Draft Email**: Create and store email drafts for later use
- **Search Email**: Search through sent emails and drafts
- **Duplicate Prevention**: Automatically detects and prevents duplicate emails
- **DRY_RUN Mode**: Test without sending actual emails
- **Comprehensive Logging**: All actions logged to `/Logs/YYYY-MM-DD.json`
- **Schema Validation**: Input validation using Zod
- **Error Handling**: Robust error handling with detailed logging

## Installation

```bash
cd mcp_servers/email_mcp
npm install
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your SMTP credentials:

```env
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Server Configuration
DRY_RUN=false
LOG_LEVEL=info

# Default Sender
DEFAULT_FROM=your-email@gmail.com
DEFAULT_FROM_NAME=AI Employee
```

### Gmail Setup

For Gmail, you need to use an **App Password**:

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use this password in `SMTP_PASS`

### Other Email Providers

**Outlook/Office365:**
```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_SECURE=false
```

**Yahoo:**
```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_SECURE=false
```

**Custom SMTP:**
```env
SMTP_HOST=your-smtp-server.com
SMTP_PORT=465
SMTP_SECURE=true
```

## Usage

### Running the Server

```bash
npm start
```

### Development Mode (with auto-reload)

```bash
npm run dev
```

### Integrating with Claude Code Router

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "email": {
      "command": "node",
      "args": ["/absolute/path/to/mcp_servers/email_mcp/index.js"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "your-email@gmail.com",
        "SMTP_PASS": "your-app-password",
        "DRY_RUN": "false"
      }
    }
  }
}
```

## Available Tools

### 1. send_email

Send an email with full validation and duplicate prevention.

**Parameters:**
- `to` (required): Email address or array of addresses
- `subject` (required): Email subject (max 998 chars)
- `body` (required): Email body content
- `cc` (optional): CC recipients
- `bcc` (optional): BCC recipients
- `from` (optional): Sender address (defaults to configured sender)
- `html` (optional): Whether body is HTML (default: false)

**Example:**
```json
{
  "to": "recipient@example.com",
  "subject": "Meeting Reminder",
  "body": "Don't forget our meeting tomorrow at 10 AM.",
  "cc": ["manager@example.com"],
  "html": false
}
```

**Response:**
```json
{
  "success": true,
  "emailId": "sent_1234567890_abc123",
  "messageId": "<unique-message-id@smtp.gmail.com>",
  "dryRun": false,
  "message": "Email sent successfully",
  "timestamp": "2026-02-24T10:30:00.000Z"
}
```

### 2. draft_email

Create an email draft for later review or sending.

**Parameters:**
- `to` (optional): Email address or array of addresses
- `subject` (optional): Email subject
- `body` (optional): Email body content
- `cc` (optional): CC recipients
- `bcc` (optional): BCC recipients
- `from` (optional): Sender address

**Example:**
```json
{
  "to": "client@example.com",
  "subject": "Project Proposal",
  "body": "Draft content here..."
}
```

**Response:**
```json
{
  "success": true,
  "draftId": "draft_1234567890_xyz789",
  "message": "Draft created successfully",
  "draft": {
    "to": "client@example.com",
    "subject": "Project Proposal",
    "body": "Draft content here...",
    "id": "draft_1234567890_xyz789"
  },
  "timestamp": "2026-02-24T10:30:00.000Z"
}
```

### 3. search_email

Search through sent emails and drafts.

**Parameters:**
- `query` (required): Search query string
- `type` (optional): "sent", "draft", or "all" (default: "all")
- `limit` (optional): Max results, 1-100 (default: 10)

**Example:**
```json
{
  "query": "meeting",
  "type": "all",
  "limit": 5
}
```

**Response:**
```json
{
  "success": true,
  "query": "meeting",
  "type": "all",
  "count": 2,
  "results": [
    {
      "id": "sent_1234567890_abc123",
      "to": "recipient@example.com",
      "subject": "Meeting Reminder",
      "body": "Don't forget our meeting...",
      "timestamp": "2026-02-24T10:30:00.000Z",
      "type": "sent"
    }
  ]
}
```

## Features in Detail

### Duplicate Prevention

The server automatically detects duplicate emails based on:
- Recipient(s)
- Subject line
- First 500 characters of body

If a duplicate is detected, the email will not be sent and you'll receive a warning.

### DRY_RUN Mode

Set `DRY_RUN=true` to test the server without sending actual emails. All operations will be logged, but no SMTP connections will be made.

### Logging

All actions are logged to `/Logs/YYYY-MM-DD.json` with the following information:
- Timestamp
- Action type
- Success/failure status
- Email details (recipients, subject)
- Error messages (if any)

**Log Entry Example:**
```json
{
  "timestamp": "2026-02-24T10:30:00.000Z",
  "level": "info",
  "action": "email_sent",
  "messageId": "<unique-id@smtp.gmail.com>",
  "to": "recipient@example.com",
  "subject": "Meeting Reminder",
  "response": "250 2.0.0 OK"
}
```

### Error Handling

The server provides detailed error messages for:
- Invalid email addresses
- Missing required fields
- SMTP connection failures
- Authentication errors
- Network timeouts

All errors are logged with full stack traces for debugging.

## Troubleshooting

### "SMTP credentials not configured"

**Solution:** Set `SMTP_USER` and `SMTP_PASS` environment variables.

### "Invalid login: 535 Authentication failed"

**Solutions:**
- For Gmail: Use an App Password, not your regular password
- Verify credentials are correct
- Check if 2FA is enabled (required for Gmail App Passwords)

### "Connection timeout"

**Solutions:**
- Check firewall settings
- Verify SMTP host and port are correct
- Try different port (587 or 465)
- Check if `SMTP_SECURE` matches the port (465 = true, 587 = false)

### "Duplicate email detected"

**Solution:** This is intentional. The server prevents sending identical emails. If you need to resend, modify the subject or body slightly.

### Logs not being created

**Solutions:**
- Check `LOGS_DIR` path in `.env`
- Ensure write permissions for the logs directory
- Verify the path is relative to the server's location

## Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use App Passwords** - Don't use your main email password
3. **Enable DRY_RUN** - Test thoroughly before sending real emails
4. **Review logs regularly** - Monitor for unauthorized access attempts
5. **Limit BCC usage** - Be mindful of privacy when using BCC
6. **Validate recipients** - The server validates email formats, but verify recipients are correct

## Development

### Project Structure

```
email_mcp/
├── index.js          # Main server implementation
├── package.json      # Dependencies and scripts
├── .env.example      # Example configuration
├── .env              # Your configuration (not in git)
└── README.md         # This file
```

### Dependencies

- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `nodemailer` - SMTP email sending
- `zod` - Schema validation

### Extending the Server

To add new tools:

1. Define a Zod schema for validation
2. Add tool definition in `ListToolsRequestSchema` handler
3. Implement tool logic in `CallToolRequestSchema` handler
4. Add logging for the new action

## License

MIT

## Support

For issues or questions:
- Check the troubleshooting section above
- Review logs in `/Logs/YYYY-MM-DD.json`
- Verify environment configuration
- Test with `DRY_RUN=true` first
