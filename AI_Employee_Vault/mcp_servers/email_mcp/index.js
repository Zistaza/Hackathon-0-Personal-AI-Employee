#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import nodemailer from 'nodemailer';
import { z } from 'zod';
import { createHash } from 'crypto';
import { mkdir, appendFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============================================================================
// Configuration & Environment
// ============================================================================

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
  logLevel: process.env.LOG_LEVEL || 'info',
  defaultFrom: process.env.DEFAULT_FROM || process.env.SMTP_USER,
  defaultFromName: process.env.DEFAULT_FROM_NAME || 'AI Employee',
  logsDir: process.env.LOGS_DIR || '../../Logs',
};

// ============================================================================
// Validation Schemas
// ============================================================================

const EmailAddressSchema = z.string().email('Invalid email address');

const SendEmailSchema = z.object({
  to: z.union([
    EmailAddressSchema,
    z.array(EmailAddressSchema).min(1, 'At least one recipient required'),
  ]),
  subject: z.string().min(1, 'Subject is required').max(998, 'Subject too long'),
  body: z.string().min(1, 'Body is required'),
  cc: z.union([EmailAddressSchema, z.array(EmailAddressSchema)]).optional(),
  bcc: z.union([EmailAddressSchema, z.array(EmailAddressSchema)]).optional(),
  from: EmailAddressSchema.optional(),
  html: z.boolean().optional().default(false),
});

const DraftEmailSchema = z.object({
  to: z.union([EmailAddressSchema, z.array(EmailAddressSchema)]).optional(),
  subject: z.string().max(998, 'Subject too long').optional(),
  body: z.string().optional(),
  cc: z.union([EmailAddressSchema, z.array(EmailAddressSchema)]).optional(),
  bcc: z.union([EmailAddressSchema, z.array(EmailAddressSchema)]).optional(),
  from: EmailAddressSchema.optional(),
});

const SearchEmailSchema = z.object({
  query: z.string().min(1, 'Search query is required'),
  type: z.enum(['sent', 'draft', 'all']).default('all'),
  limit: z.number().int().positive().max(100).default(10),
});

// ============================================================================
// State Management
// ============================================================================

class EmailStore {
  constructor() {
    this.sentEmails = new Map();
    this.drafts = new Map();
    this.sentHashes = new Set();
  }

  generateEmailHash(to, subject, body) {
    const normalized = JSON.stringify({
      to: Array.isArray(to) ? to.sort() : [to],
      subject: subject.trim().toLowerCase(),
      body: body.trim().substring(0, 500),
    });
    return createHash('sha256').update(normalized).digest('hex');
  }

  isDuplicate(to, subject, body) {
    const hash = this.generateEmailHash(to, subject, body);
    return this.sentHashes.has(hash);
  }

  addSentEmail(emailData) {
    const id = `sent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const hash = this.generateEmailHash(emailData.to, emailData.subject, emailData.body);

    this.sentEmails.set(id, {
      ...emailData,
      id,
      timestamp: new Date().toISOString(),
      hash,
    });

    this.sentHashes.add(hash);
    return id;
  }

  addDraft(draftData) {
    const id = `draft_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    this.drafts.set(id, {
      ...draftData,
      id,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });

    return id;
  }

  searchEmails(query, type, limit) {
    const results = [];
    const lowerQuery = query.toLowerCase();

    const searchInEmail = (email) => {
      const searchableText = [
        email.subject || '',
        email.body || '',
        Array.isArray(email.to) ? email.to.join(' ') : email.to || '',
        Array.isArray(email.cc) ? email.cc.join(' ') : email.cc || '',
      ].join(' ').toLowerCase();

      return searchableText.includes(lowerQuery);
    };

    if (type === 'sent' || type === 'all') {
      for (const email of this.sentEmails.values()) {
        if (searchInEmail(email)) {
          results.push({ ...email, type: 'sent' });
        }
        if (results.length >= limit) break;
      }
    }

    if (type === 'draft' || type === 'all') {
      for (const draft of this.drafts.values()) {
        if (searchInEmail(draft)) {
          results.push({ ...draft, type: 'draft' });
        }
        if (results.length >= limit) break;
      }
    }

    return results.slice(0, limit);
  }
}

const emailStore = new EmailStore();

// ============================================================================
// Logging
// ============================================================================

class Logger {
  constructor() {
    this.logsDir = join(__dirname, config.logsDir);
  }

  async ensureLogsDir() {
    try {
      await mkdir(this.logsDir, { recursive: true });
    } catch (error) {
      console.error('Failed to create logs directory:', error);
    }
  }

  getLogFilePath() {
    const date = new Date().toISOString().split('T')[0];
    return join(this.logsDir, `${date}.json`);
  }

  async log(level, action, data) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      action,
      ...data,
    };

    // Console output
    if (config.logLevel === 'debug' || level === 'error' || level === 'warn') {
      console.error(JSON.stringify(logEntry, null, 2));
    }

    // File output
    try {
      await this.ensureLogsDir();
      const logLine = JSON.stringify(logEntry) + '\n';
      await appendFile(this.getLogFilePath(), logLine, 'utf8');
    } catch (error) {
      console.error('Failed to write log:', error);
    }
  }

  info(action, data) {
    return this.log('info', action, data);
  }

  error(action, data) {
    return this.log('error', action, data);
  }

  warn(action, data) {
    return this.log('warn', action, data);
  }

  debug(action, data) {
    return this.log('debug', action, data);
  }
}

const logger = new Logger();

// ============================================================================
// Email Service
// ============================================================================

class EmailService {
  constructor() {
    this.transporter = null;
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;

    if (!config.smtp.auth.user || !config.smtp.auth.pass) {
      throw new Error('SMTP credentials not configured. Set SMTP_USER and SMTP_PASS environment variables.');
    }

    try {
      this.transporter = nodemailer.createTransport(config.smtp);

      if (!config.dryRun) {
        await this.transporter.verify();
        await logger.info('email_service_initialized', {
          host: config.smtp.host,
          port: config.smtp.port,
          user: config.smtp.auth.user,
        });
      } else {
        await logger.info('email_service_initialized_dry_run', {
          message: 'Running in DRY_RUN mode - no emails will be sent',
        });
      }

      this.initialized = true;
    } catch (error) {
      await logger.error('email_service_init_failed', {
        error: error.message,
        stack: error.stack,
      });
      throw new Error(`Failed to initialize email service: ${error.message}`);
    }
  }

  async sendEmail(emailData) {
    await this.initialize();

    const mailOptions = {
      from: emailData.from
        ? emailData.from
        : `"${config.defaultFromName}" <${config.defaultFrom}>`,
      to: Array.isArray(emailData.to) ? emailData.to.join(', ') : emailData.to,
      subject: emailData.subject,
      [emailData.html ? 'html' : 'text']: emailData.body,
    };

    if (emailData.cc) {
      mailOptions.cc = Array.isArray(emailData.cc) ? emailData.cc.join(', ') : emailData.cc;
    }

    if (emailData.bcc) {
      mailOptions.bcc = Array.isArray(emailData.bcc) ? emailData.bcc.join(', ') : emailData.bcc;
    }

    if (config.dryRun) {
      await logger.info('email_send_dry_run', {
        mailOptions,
        message: 'DRY_RUN mode - email not actually sent',
      });

      return {
        success: true,
        messageId: `dry_run_${Date.now()}`,
        dryRun: true,
      };
    }

    try {
      const info = await this.transporter.sendMail(mailOptions);

      await logger.info('email_sent', {
        messageId: info.messageId,
        to: mailOptions.to,
        subject: mailOptions.subject,
        response: info.response,
      });

      return {
        success: true,
        messageId: info.messageId,
        response: info.response,
      };
    } catch (error) {
      await logger.error('email_send_failed', {
        error: error.message,
        stack: error.stack,
        mailOptions: {
          to: mailOptions.to,
          subject: mailOptions.subject,
        },
      });
      throw error;
    }
  }
}

const emailService = new EmailService();

// ============================================================================
// MCP Server Implementation
// ============================================================================

const server = new Server(
  {
    name: 'email-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'send_email',
        description: 'Send an email via SMTP. Validates recipients, prevents duplicates, and logs all actions.',
        inputSchema: {
          type: 'object',
          properties: {
            to: {
              oneOf: [
                { type: 'string', format: 'email' },
                { type: 'array', items: { type: 'string', format: 'email' }, minItems: 1 },
              ],
              description: 'Recipient email address(es)',
            },
            subject: {
              type: 'string',
              minLength: 1,
              maxLength: 998,
              description: 'Email subject line',
            },
            body: {
              type: 'string',
              minLength: 1,
              description: 'Email body content',
            },
            cc: {
              oneOf: [
                { type: 'string', format: 'email' },
                { type: 'array', items: { type: 'string', format: 'email' } },
              ],
              description: 'CC recipients (optional)',
            },
            bcc: {
              oneOf: [
                { type: 'string', format: 'email' },
                { type: 'array', items: { type: 'string', format: 'email' } },
              ],
              description: 'BCC recipients (optional)',
            },
            from: {
              type: 'string',
              format: 'email',
              description: 'Sender email address (optional, defaults to configured sender)',
            },
            html: {
              type: 'boolean',
              description: 'Whether body contains HTML (default: false)',
            },
          },
          required: ['to', 'subject', 'body'],
        },
      },
      {
        name: 'draft_email',
        description: 'Create an email draft for later review or sending. Drafts are stored in memory and can be searched.',
        inputSchema: {
          type: 'object',
          properties: {
            to: {
              oneOf: [
                { type: 'string', format: 'email' },
                { type: 'array', items: { type: 'string', format: 'email' } },
              ],
              description: 'Recipient email address(es) (optional)',
            },
            subject: {
              type: 'string',
              maxLength: 998,
              description: 'Email subject line (optional)',
            },
            body: {
              type: 'string',
              description: 'Email body content (optional)',
            },
            cc: {
              oneOf: [
                { type: 'string', format: 'email' },
                { type: 'array', items: { type: 'string', format: 'email' } },
              ],
              description: 'CC recipients (optional)',
            },
            bcc: {
              oneOf: [
                { type: 'string', format: 'email' },
                { type: 'array', items: { type: 'string', format: 'email' } },
              ],
              description: 'BCC recipients (optional)',
            },
            from: {
              type: 'string',
              format: 'email',
              description: 'Sender email address (optional)',
            },
          },
        },
      },
      {
        name: 'search_email',
        description: 'Search through sent emails and drafts. Returns matching results with full details.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              minLength: 1,
              description: 'Search query (searches in subject, body, to, cc fields)',
            },
            type: {
              type: 'string',
              enum: ['sent', 'draft', 'all'],
              description: 'Type of emails to search (default: all)',
            },
            limit: {
              type: 'number',
              minimum: 1,
              maximum: 100,
              description: 'Maximum number of results (default: 10)',
            },
          },
          required: ['query'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'send_email': {
        // Validate input
        const validatedArgs = SendEmailSchema.parse(args);

        // Check for duplicates
        if (emailStore.isDuplicate(validatedArgs.to, validatedArgs.subject, validatedArgs.body)) {
          await logger.warn('duplicate_email_prevented', {
            to: validatedArgs.to,
            subject: validatedArgs.subject,
          });

          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  success: false,
                  error: 'Duplicate email detected',
                  message: 'An identical email (same recipient, subject, and body) was already sent recently.',
                }, null, 2),
              },
            ],
          };
        }

        // Send email
        const result = await emailService.sendEmail(validatedArgs);

        // Store in sent emails
        const emailId = emailStore.addSentEmail({
          ...validatedArgs,
          messageId: result.messageId,
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                emailId,
                messageId: result.messageId,
                dryRun: result.dryRun || false,
                message: result.dryRun
                  ? 'Email prepared successfully (DRY_RUN mode - not actually sent)'
                  : 'Email sent successfully',
                timestamp: new Date().toISOString(),
              }, null, 2),
            },
          ],
        };
      }

      case 'draft_email': {
        // Validate input
        const validatedArgs = DraftEmailSchema.parse(args);

        // Create draft
        const draftId = emailStore.addDraft(validatedArgs);

        await logger.info('draft_created', {
          draftId,
          hasSubject: !!validatedArgs.subject,
          hasBody: !!validatedArgs.body,
          hasRecipients: !!validatedArgs.to,
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                draftId,
                message: 'Draft created successfully',
                draft: {
                  ...validatedArgs,
                  id: draftId,
                },
                timestamp: new Date().toISOString(),
              }, null, 2),
            },
          ],
        };
      }

      case 'search_email': {
        // Validate input
        const validatedArgs = SearchEmailSchema.parse(args);

        // Search emails
        const results = emailStore.searchEmails(
          validatedArgs.query,
          validatedArgs.type,
          validatedArgs.limit
        );

        await logger.info('email_search', {
          query: validatedArgs.query,
          type: validatedArgs.type,
          resultsCount: results.length,
        });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                query: validatedArgs.query,
                type: validatedArgs.type,
                count: results.length,
                results,
              }, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    await logger.error('tool_execution_error', {
      tool: name,
      error: error.message,
      stack: error.stack,
      args,
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error.message,
            tool: name,
          }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// ============================================================================
// Server Startup
// ============================================================================

async function main() {
  try {
    await logger.info('server_starting', {
      version: '1.0.0',
      dryRun: config.dryRun,
      smtpHost: config.smtp.host,
      smtpPort: config.smtp.port,
    });

    const transport = new StdioServerTransport();
    await server.connect(transport);

    await logger.info('server_started', {
      message: 'Email MCP Server is running',
    });
  } catch (error) {
    await logger.error('server_startup_failed', {
      error: error.message,
      stack: error.stack,
    });
    process.exit(1);
  }
}

main();
