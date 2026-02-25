const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

class WhatsAppWatcher {
  constructor(config) {
    this.config = config;
    this.processedIds = new Set();
    this.keywords = config.keywords.map(k => k.toLowerCase());
    this.browser = null;
    this.context = null;
    this.page = null;
  }

  async initialize() {
    await this.loadProcessedIds();
    await this.ensureDirectories();
  }

  async loadProcessedIds() {
    try {
      const data = await fs.readFile(this.config.processedIdsFile, 'utf8');
      const ids = JSON.parse(data);
      this.processedIds = new Set(ids);
    } catch (error) {
      this.processedIds = new Set();
    }
  }

  async saveProcessedIds() {
    const ids = Array.from(this.processedIds);
    await fs.writeFile(
      this.config.processedIdsFile,
      JSON.stringify(ids, null, 2),
      'utf8'
    );
  }

  async ensureDirectories() {
    const dirs = [
      this.config.needsActionDir,
      this.config.logsDir,
      this.config.userDataDir,
      path.dirname(this.config.processedIdsFile)
    ];

    for (const dir of dirs) {
      await fs.mkdir(dir, { recursive: true });
    }
  }

  async log(message) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${message}\n`;
    const logFile = path.join(this.config.logsDir, 'whatsapp_watcher.log');

    console.log(logEntry.trim());
    await fs.appendFile(logFile, logEntry, 'utf8');
  }

  async createActionFile(messageData) {
    const timestamp = Date.now();
    const filename = `whatsapp_${timestamp}.md`;
    const filepath = path.join(this.config.needsActionDir, filename);

    const content = `---
type: whatsapp
sender: ${messageData.sender}
timestamp: ${messageData.timestamp}
status: pending
---

${messageData.content}
`;

    await fs.writeFile(filepath, content, 'utf8');
    await this.log(`Created action file: ${filename} for sender: ${messageData.sender}`);

    return filename;
  }

  containsKeyword(text) {
    const lowerText = text.toLowerCase();
    return this.keywords.some(keyword => lowerText.includes(keyword));
  }

  async launchBrowser() {
    await this.log('Launching browser with persistent context...');

    const userDataDir = path.resolve(this.config.userDataDir);

    this.context = await chromium.launchPersistentContext(userDataDir, {
      headless: this.config.headless || false,
      viewport: this.config.viewport || { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    this.page = this.context.pages()[0] || await this.context.newPage();
  }

  async navigateToWhatsApp() {
    await this.log('Navigating to WhatsApp Web...');
    await this.page.goto('https://web.whatsapp.com', { waitUntil: 'networkidle' });
  }

  async waitForWhatsAppLoad() {
    await this.log('Waiting for WhatsApp to load...');

    try {
      // Wait for either QR code (not logged in) or chat list (logged in)
      await this.page.waitForSelector('canvas[aria-label="Scan me!"], [data-testid="chat-list"]', {
        timeout: 30000
      });

      // Check if QR code is present
      const qrCode = await this.page.$('canvas[aria-label="Scan me!"]');

      if (qrCode) {
        await this.log('QR code detected. Please scan to login...');
        // Wait for login to complete
        await this.page.waitForSelector('[data-testid="chat-list"]', {
          timeout: this.config.loginTimeout || 120000
        });
        await this.log('Login successful!');
      } else {
        await this.log('Already logged in via saved session');
      }

      // Additional wait for full load
      await this.page.waitForTimeout(3000);

    } catch (error) {
      throw new Error(`Failed to load WhatsApp: ${error.message}`);
    }
  }

  async getUnreadChats() {
    await this.log('Scanning for unread chats...');

    try {
      // Find all chat elements with unread indicators
      const chats = await this.page.$$('[data-testid="cell-frame-container"]');
      const unreadChats = [];

      for (const chat of chats) {
        try {
          // Check for unread badge
          const unreadBadge = await chat.$('[data-testid="icon-unread-count"]');

          if (unreadBadge) {
            // Get chat name
            const nameElement = await chat.$('[data-testid="cell-frame-title"]');
            const name = nameElement ? await nameElement.textContent() : 'Unknown';

            // Get chat ID from aria-label or data attribute
            const chatId = await chat.getAttribute('data-id') || `chat_${Date.now()}_${Math.random()}`;

            unreadChats.push({
              element: chat,
              id: chatId,
              name: name.trim()
            });
          }
        } catch (error) {
          // Skip this chat if we can't parse it
          continue;
        }
      }

      return unreadChats;

    } catch (error) {
      await this.log(`Error getting unread chats: ${error.message}`);
      return [];
    }
  }

  async processChat(chat) {
    try {
      await this.log(`Processing chat: ${chat.name}`);

      // Click on the chat to open it
      await chat.element.click();
      await this.page.waitForTimeout(this.config.waitAfterClick || 2000);

      // Get all message bubbles in the chat
      const messages = await this.getMessagesFromChat();

      let matchCount = 0;

      for (const message of messages) {
        const messageId = `${chat.id}_${message.timestamp}_${message.content.substring(0, 50)}`;

        // Skip if already processed
        if (this.processedIds.has(messageId)) {
          continue;
        }

        // Check if message contains keywords
        if (this.containsKeyword(message.content)) {
          await this.log(`Keyword match found in message from ${chat.name}`);

          const messageData = {
            sender: chat.name,
            timestamp: new Date(message.timestamp).toISOString(),
            content: message.content
          };

          await this.createActionFile(messageData);

          this.processedIds.add(messageId);
          await this.saveProcessedIds();
          matchCount++;
        }
      }

      if (matchCount > 0) {
        await this.log(`Created ${matchCount} action file(s) from ${chat.name}`);
      }

    } catch (error) {
      await this.log(`Error processing chat ${chat.name}: ${error.message}`);
    }
  }

  async getMessagesFromChat() {
    try {
      // Get message bubbles (incoming messages only)
      const messageElements = await this.page.$$('[data-testid="msg-container"]');
      const messages = [];

      // Process only recent messages (configurable limit)
      const maxMessages = this.config.maxMessagesPerChat || 20;
      const recentMessages = messageElements.slice(-maxMessages);

      for (const msgElement of recentMessages) {
        try {
          // Check if it's an incoming message (not sent by user)
          const isIncoming = await msgElement.$('[data-testid="msg-container"] [data-testid="tail-in"]');

          if (!isIncoming) {
            continue; // Skip outgoing messages
          }

          // Get message text
          const textElement = await msgElement.$('[data-testid="conversation-text-content"]');
          if (!textElement) {
            continue;
          }

          const content = await textElement.textContent();

          // Get timestamp
          const timeElement = await msgElement.$('[data-testid="msg-meta"]');
          const timeText = timeElement ? await timeElement.textContent() : '';

          messages.push({
            content: content.trim(),
            timestamp: Date.now(), // Use current time as approximation
            timeText: timeText.trim()
          });

        } catch (error) {
          // Skip messages we can't parse
          continue;
        }
      }

      return messages;

    } catch (error) {
      await this.log(`Error extracting messages: ${error.message}`);
      return [];
    }
  }

  async closeBrowser() {
    if (this.context) {
      await this.log('Closing browser...');
      await this.context.close();
    }
  }

  async scanWhatsApp(retryCount = 0) {
    try {
      await this.log('Starting WhatsApp scan...');

      await this.launchBrowser();
      await this.navigateToWhatsApp();
      await this.waitForWhatsAppLoad();

      const unreadChats = await this.getUnreadChats();
      await this.log(`Found ${unreadChats.length} unread chat(s)`);

      for (const chat of unreadChats) {
        await this.processChat(chat);
      }

      await this.log('WhatsApp scan completed successfully');

    } catch (error) {
      await this.log(`Error during scan: ${error.message}`);

      if (retryCount < this.config.maxRetries) {
        await this.log(`Retrying... (${retryCount + 1}/${this.config.maxRetries})`);
        await this.sleep(this.config.retryDelay);
        return this.scanWhatsApp(retryCount + 1);
      } else {
        await this.log(`Max retries reached. Scan failed.`);
        throw error;
      }
    } finally {
      await this.closeBrowser();
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async run() {
    try {
      await this.initialize();
      await this.scanWhatsApp();
    } catch (error) {
      await this.log(`Fatal error: ${error.message}`);
      throw error;
    }
  }
}

// Load configuration
function loadConfig() {
  try {
    const configFile = path.join(__dirname, 'config.json');
    const configData = require('fs').readFileSync(configFile, 'utf8');
    const config = JSON.parse(configData);

    return {
      keywords: config.keywords,
      needsActionDir: path.join(__dirname, config.paths.needsActionDir),
      logsDir: path.join(__dirname, config.paths.logsDir),
      processedIdsFile: path.join(__dirname, config.paths.processedIdsFile),
      userDataDir: path.join(__dirname, config.paths.userDataDir),
      maxRetries: config.retry.maxRetries,
      retryDelay: config.retry.retryDelay,
      headless: config.browser.headless,
      viewport: config.browser.viewport,
      maxMessagesPerChat: config.scanning.maxMessagesPerChat,
      waitAfterClick: config.scanning.waitAfterClick,
      loginTimeout: config.scanning.loginTimeout
    };
  } catch (error) {
    console.error('Failed to load config.json, using defaults:', error.message);
    return {
      keywords: ['invoice', 'urgent', 'payment', 'proposal'],
      needsActionDir: path.join(__dirname, '../../Needs_Action'),
      logsDir: path.join(__dirname, '../../Logs'),
      processedIdsFile: path.join(__dirname, 'processed_ids.json'),
      userDataDir: path.join(__dirname, 'whatsapp_session'),
      maxRetries: 3,
      retryDelay: 5000
    };
  }
}

// Main execution
if (require.main === module) {
  const config = loadConfig();
  const watcher = new WhatsAppWatcher(config);
  watcher.run().catch(console.error);
}

module.exports = WhatsAppWatcher;
