#!/usr/bin/env node

import nodemailer from 'nodemailer';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, '.env') });

const config = {
  smtp: {
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: process.env.SMTP_SECURE === 'true',
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  },
  dryRun: process.env.DRY_RUN === 'true',
  defaultFrom: process.env.DEFAULT_FROM || process.env.SMTP_USER,
  defaultFromName: process.env.DEFAULT_FROM_NAME || 'AI Employee',
};

async function sendTestEmail(to) {
  console.log('📧 Email MCP Test\n');
  console.log('Configuration:');
  console.log(`  SMTP Host: ${config.smtp.host}`);
  console.log(`  SMTP Port: ${config.smtp.port}`);
  console.log(`  SMTP User: ${config.smtp.auth.user}`);
  console.log(`  DRY RUN: ${config.dryRun ? 'YES ✓' : 'NO'}`);
  console.log(`  To: ${to}\n`);

  if (!config.smtp.auth.user || !config.smtp.auth.pass) {
    console.error('❌ Error: SMTP credentials not configured');
    console.error('Please set SMTP_USER and SMTP_PASS in .env file');
    process.exit(1);
  }

  const transporter = nodemailer.createTransport(config.smtp);

  const mailOptions = {
    from: `"${config.defaultFromName}" <${config.defaultFrom}>`,
    to: to,
    subject: '🤖 Test Email from AI Employee Email MCP',
    text: `Hello!

This is a test email from the AI Employee Email MCP Server.

If you're receiving this, it means the email system is working correctly!

Test Details:
- Sent at: ${new Date().toISOString()}
- From: ${config.defaultFrom}
- SMTP Host: ${config.smtp.host}
- DRY RUN Mode: ${config.dryRun ? 'YES' : 'NO'}

Best regards,
AI Employee System`,
    html: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">🤖 Test Email from AI Employee Email MCP</h2>
        <p>Hello!</p>
        <p>This is a test email from the <strong>AI Employee Email MCP Server</strong>.</p>
        <p>If you're receiving this, it means the email system is working correctly! ✓</p>

        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
          <h3 style="margin-top: 0; color: #374151;">Test Details:</h3>
          <ul style="color: #6b7280;">
            <li><strong>Sent at:</strong> ${new Date().toISOString()}</li>
            <li><strong>From:</strong> ${config.defaultFrom}</li>
            <li><strong>SMTP Host:</strong> ${config.smtp.host}</li>
            <li><strong>DRY RUN Mode:</strong> ${config.dryRun ? 'YES' : 'NO'}</li>
          </ul>
        </div>

        <p style="color: #6b7280; font-size: 14px;">
          Best regards,<br>
          <strong>AI Employee System</strong>
        </p>
      </div>
    `,
  };

  if (config.dryRun) {
    console.log('🔍 DRY RUN MODE - Email will NOT be sent\n');
    console.log('Email Preview:');
    console.log('─'.repeat(50));
    console.log(`From: ${mailOptions.from}`);
    console.log(`To: ${mailOptions.to}`);
    console.log(`Subject: ${mailOptions.subject}`);
    console.log('─'.repeat(50));
    console.log(mailOptions.text);
    console.log('─'.repeat(50));
    console.log('\n✓ DRY RUN completed successfully');
    console.log('💡 To send real emails, set DRY_RUN=false in .env file');
    return;
  }

  try {
    console.log('🔄 Verifying SMTP connection...');
    await transporter.verify();
    console.log('✓ SMTP connection verified\n');

    console.log('📤 Sending email...');
    const info = await transporter.sendMail(mailOptions);

    console.log('\n✓ Email sent successfully!');
    console.log(`Message ID: ${info.messageId}`);
    console.log(`Response: ${info.response}`);
  } catch (error) {
    console.error('\n❌ Error sending email:');
    console.error(error.message);

    if (error.message.includes('Invalid login')) {
      console.error('\n💡 Tip: For Gmail, you need to use an App Password:');
      console.error('   1. Enable 2FA on your Google account');
      console.error('   2. Go to https://myaccount.google.com/apppasswords');
      console.error('   3. Generate an app password for "Mail"');
      console.error('   4. Use that password in SMTP_PASS');
    }

    process.exit(1);
  }
}

// Get recipient from command line or use default
const recipient = process.argv[2] || 'zinatyamin@gmail.com';
sendTestEmail(recipient);
