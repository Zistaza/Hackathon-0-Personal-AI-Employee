#!/usr/bin/env node
/**
 * Gmail Watcher Skill - Silver Tier
 * Monitors Gmail for unread important emails and creates action items
 */

const fs = require('fs').promises;
const path = require('path');
const { google } = require('googleapis');
const { spawn } = require('child_process');

// Configuration
const CONFIG = {
  CREDENTIALS_PATH: path.join(__dirname, '../../credentials.json'),
  TOKEN_PATH: path.join(__dirname, 'token.json'),
  PROCESSED_IDS_PATH: path.join(__dirname, 'processed_ids.json'),
  NEEDS_ACTION_DIR: path.join(__dirname, '../../Needs_Action'),
  LOGS_DIR: path.join(__dirname, '../../Logs'),
  APPEND_LOG_SCRIPT: path.join(__dirname, '../process_needs_action/append_log.py'),
  SCOPES: ['https://www.googleapis.com/auth/gmail.readonly']
};

/**
 * Load or initialize processed email IDs
 */
async function loadProcessedIds() {
  try {
    const data = await fs.readFile(CONFIG.PROCESSED_IDS_PATH, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return { processed_ids: [], last_check: null };
  }
}

/**
 * Save processed email IDs
 */
async function saveProcessedIds(data) {
  await fs.writeFile(
    CONFIG.PROCESSED_IDS_PATH,
    JSON.stringify(data, null, 2),
    'utf8'
  );
}

/**
 * Authorize Gmail API client
 */
async function authorize() {
  const credentials = JSON.parse(
    await fs.readFile(CONFIG.CREDENTIALS_PATH, 'utf8')
  );

  const { client_secret, client_id, redirect_uris } = credentials.installed;
  const oAuth2Client = new google.auth.OAuth2(
    client_id,
    client_secret,
    redirect_uris[0]
  );

  try {
    const token = await fs.readFile(CONFIG.TOKEN_PATH, 'utf8');
    oAuth2Client.setCredentials(JSON.parse(token));
    return oAuth2Client;
  } catch (error) {
    return await getNewToken(oAuth2Client);
  }
}

/**
 * Get new OAuth token (first-time setup)
 */
async function getNewToken(oAuth2Client) {
  const authUrl = oAuth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: CONFIG.SCOPES,
  });

  console.log('Authorize this app by visiting this url:', authUrl);
  console.log('\nAfter authorization, run this script again.');
  process.exit(1);
}

/**
 * Fetch unread important emails from Gmail
 */
async function fetchUnreadImportantEmails(auth) {
  const gmail = google.gmail({ version: 'v1', auth });

  const response = await gmail.users.messages.list({
    userId: 'me',
    q: 'is:unread is:important',
    maxResults: 10
  });

  const messages = response.data.messages || [];
  const emailDetails = [];

  for (const message of messages) {
    const detail = await gmail.users.messages.get({
      userId: 'me',
      id: message.id,
      format: 'full'
    });

    const headers = detail.data.payload.headers;
    const subject = headers.find(h => h.name === 'Subject')?.value || 'No Subject';
    const from = headers.find(h => h.name === 'From')?.value || 'Unknown';
    const date = headers.find(h => h.name === 'Date')?.value || new Date().toISOString();

    // Extract email body
    let body = '';
    if (detail.data.payload.parts) {
      const textPart = detail.data.payload.parts.find(
        part => part.mimeType === 'text/plain'
      );
      if (textPart && textPart.body.data) {
        body = Buffer.from(textPart.body.data, 'base64').toString('utf8');
      }
    } else if (detail.data.payload.body.data) {
      body = Buffer.from(detail.data.payload.body.data, 'base64').toString('utf8');
    }

    emailDetails.push({
      id: message.id,
      subject,
      from,
      date,
      body: body.substring(0, 2000) // Limit body length
    });
  }

  return emailDetails;
}

/**
 * Create markdown file in Needs_Action folder
 */
async function createActionFile(email) {
  const timestamp = new Date().toISOString();
  const filename = `email_${email.id}.md`;
  const filepath = path.join(CONFIG.NEEDS_ACTION_DIR, filename);

  // Parse received date
  const receivedDate = new Date(email.date).toISOString();

  const content = `---
type: email
from: ${email.from}
subject: ${email.subject}
received: ${receivedDate}
status: pending
email_id: ${email.id}
created: ${timestamp}
---

# Email: ${email.subject}

## From
${email.from}

## Received
${receivedDate}

## Content

${email.body}

---

*This email requires action. Review and create a plan in the process_needs_action workflow.*
`;

  await fs.writeFile(filepath, content, 'utf8');
  return filename;
}

/**
 * Log action using append_log.py
 */
async function logAction(actionData) {
  return new Promise((resolve, reject) => {
    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(CONFIG.LOGS_DIR, `${today}.json`);

    const logEntry = JSON.stringify({
      timestamp: new Date().toISOString(),
      action_type: 'gmail_watcher',
      ...actionData
    });

    const process = spawn('python3', [
      CONFIG.APPEND_LOG_SCRIPT,
      logFile,
      logEntry
    ]);

    let output = '';
    let errorOutput = '';

    process.stdout.on('data', (data) => {
      output += data.toString();
    });

    process.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    process.on('close', (code) => {
      if (code === 0) {
        resolve(output);
      } else {
        reject(new Error(`Logging failed: ${errorOutput}`));
      }
    });
  });
}

/**
 * Main execution
 */
async function main() {
  console.log('🔍 Gmail Watcher Skill - Starting...\n');

  try {
    // Load processed IDs
    const processedData = await loadProcessedIds();
    console.log(`✓ Loaded ${processedData.processed_ids.length} processed email IDs`);

    // Authorize Gmail API
    console.log('✓ Authorizing Gmail API...');
    const auth = await authorize();

    // Fetch unread important emails
    console.log('✓ Fetching unread important emails...');
    const emails = await fetchUnreadImportantEmails(auth);
    console.log(`✓ Found ${emails.length} unread important emails\n`);

    // Process new emails
    let processedCount = 0;
    let skippedCount = 0;

    for (const email of emails) {
      // Skip if already processed
      if (processedData.processed_ids.includes(email.id)) {
        console.log(`⊘ Skipped (already processed): ${email.subject}`);
        skippedCount++;
        continue;
      }

      try {
        // Create action file
        const filename = await createActionFile(email);
        console.log(`✓ Created: ${filename}`);

        // Add to processed IDs
        processedData.processed_ids.push(email.id);

        // Log action
        await logAction({
          email_id: email.id,
          subject: email.subject,
          from: email.from,
          file_created: filename,
          result: 'success'
        });

        processedCount++;
      } catch (error) {
        console.error(`✗ Error processing email ${email.id}:`, error.message);

        // Log error
        await logAction({
          email_id: email.id,
          subject: email.subject,
          result: 'error',
          error: error.message
        });
      }
    }

    // Update processed IDs file
    processedData.last_check = new Date().toISOString();
    await saveProcessedIds(processedData);

    // Summary
    console.log('\n📊 Summary:');
    console.log(`   Processed: ${processedCount} new emails`);
    console.log(`   Skipped: ${skippedCount} already processed`);
    console.log(`   Total tracked: ${processedData.processed_ids.length} emails`);
    console.log(`   Last check: ${processedData.last_check}`);
    console.log('\n✅ Gmail Watcher Skill - Complete');

  } catch (error) {
    console.error('\n✗ Fatal error:', error.message);

    // Log fatal error
    try {
      await logAction({
        result: 'fatal_error',
        error: error.message,
        stack: error.stack
      });
    } catch (logError) {
      console.error('✗ Could not log error:', logError.message);
    }

    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { main };
