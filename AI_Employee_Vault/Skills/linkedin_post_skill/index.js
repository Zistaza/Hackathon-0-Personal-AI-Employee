const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

class LinkedInPostSkill {
  constructor(config) {
    this.config = config;
    this.browser = null;
    this.context = null;
    this.page = null;
    this.companyTone = null;
  }

  async initialize() {
    await this.ensureDirectories();
    await this.loadCompanyHandbook();
  }

  async ensureDirectories() {
    const dirs = [
      this.config.pendingApprovalDir,
      this.config.logsDir,
      this.config.userDataDir,
      this.config.postedDir
    ];

    for (const dir of dirs) {
      await fs.mkdir(dir, { recursive: true });
    }
  }

  async loadCompanyHandbook() {
    try {
      const handbookPath = path.join(__dirname, this.config.handbookPath);
      this.companyTone = await fs.readFile(handbookPath, 'utf8');
      await this.log('Company handbook loaded successfully');
    } catch (error) {
      await this.log(`Warning: Could not load company handbook: ${error.message}`);
      this.companyTone = null;
    }
  }

  async log(message) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${message}\n`;
    const logFile = path.join(this.config.logsDir, 'linkedin_post.log');

    console.log(logEntry.trim());
    await fs.appendFile(logFile, logEntry, 'utf8');
  }

  async createDraft(postContent, metadata = {}) {
    const timestamp = Date.now();
    const filename = `linkedin_draft_${timestamp}.md`;
    const filepath = path.join(this.config.pendingApprovalDir, filename);

    const content = `---
type: linkedin_post
status: pending_approval
created: ${new Date().toISOString()}
topic: ${metadata.topic || 'General'}
dry_run: ${this.config.dryRun}
---

${postContent}

---
APPROVAL INSTRUCTIONS:
- Review the post above
- To approve: Change status to "approved" in the metadata
- To reject: Change status to "rejected" or delete this file
- To edit: Modify the post content directly
---
`;

    await fs.writeFile(filepath, content, 'utf8');
    await this.log(`Draft created: ${filename}`);

    return { filename, filepath };
  }

  async generatePost(topic, keyPoints = []) {
    await this.log(`Generating post for topic: ${topic}`);

    // Basic post generation with company tone consideration
    let post = '';

    if (this.companyTone) {
      post += `📢 ${topic}\n\n`;
    } else {
      post += `${topic}\n\n`;
    }

    if (keyPoints.length > 0) {
      keyPoints.forEach((point, index) => {
        post += `${index + 1}. ${point}\n`;
      });
      post += '\n';
    }

    // Add company-specific closing if handbook exists
    if (this.companyTone) {
      post += `What are your thoughts? Share in the comments below.\n\n`;
      post += `#Business #Leadership #Innovation`;
    }

    return post;
  }

  async getPendingApprovals() {
    try {
      const files = await fs.readdir(this.config.pendingApprovalDir);
      const drafts = [];

      for (const file of files) {
        if (file.endsWith('.md')) {
          const filepath = path.join(this.config.pendingApprovalDir, file);
          const content = await fs.readFile(filepath, 'utf8');

          // Parse metadata
          const metadataMatch = content.match(/---\n([\s\S]*?)\n---/);
          if (metadataMatch) {
            const metadata = this.parseMetadata(metadataMatch[1]);

            if (metadata.status === 'approved') {
              drafts.push({
                filename: file,
                filepath,
                content,
                metadata
              });
            }
          }
        }
      }

      return drafts;
    } catch (error) {
      await this.log(`Error reading pending approvals: ${error.message}`);
      return [];
    }
  }

  parseMetadata(metadataText) {
    const metadata = {};
    const lines = metadataText.split('\n');

    for (const line of lines) {
      const match = line.match(/^(\w+):\s*(.+)$/);
      if (match) {
        metadata[match[1]] = match[2].trim();
      }
    }

    return metadata;
  }

  extractPostContent(fullContent) {
    // Extract content between first --- block and approval instructions
    const parts = fullContent.split('---');
    if (parts.length >= 3) {
      return parts[2].trim();
    }
    return fullContent;
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

  async navigateToLinkedIn() {
    await this.log('Navigating to LinkedIn...');
    await this.page.goto('https://www.linkedin.com', { waitUntil: 'networkidle' });
  }

  async waitForLinkedInLoad() {
    await this.log('Waiting for LinkedIn to load...');

    try {
      // Wait for either login form or feed (already logged in)
      await this.page.waitForSelector('input[name="session_key"], [data-test-id="feed-container"]', {
        timeout: 30000
      });

      // Check if login is required
      const loginForm = await this.page.$('input[name="session_key"]');

      if (loginForm) {
        await this.log('Login required. Please login manually...');
        // Wait for successful login
        await this.page.waitForSelector('[data-test-id="feed-container"]', { timeout: 300000 });
        await this.log('Login successful!');
      } else {
        await this.log('Already logged in via saved session');
      }

      await this.page.waitForTimeout(2000);

    } catch (error) {
      throw new Error(`Failed to load LinkedIn: ${error.message}`);
    }
  }

  async postToLinkedIn(postContent) {
    try {
      await this.log('Starting post creation...');

      // Click "Start a post" button
      const startPostButton = await this.page.waitForSelector('[data-test-id="share-box-open"], .share-box-feed-entry__trigger', {
        timeout: 10000
      });
      await startPostButton.click();
      await this.page.waitForTimeout(1500);

      // Wait for the post editor to appear
      await this.page.waitForSelector('.ql-editor, [data-placeholder="What do you want to talk about?"]', {
        timeout: 10000
      });

      // Type the post content
      const editor = await this.page.$('.ql-editor, [data-placeholder="What do you want to talk about?"]');
      await editor.click();
      await this.page.waitForTimeout(500);

      // Type content line by line to preserve formatting
      const lines = postContent.split('\n');
      for (let i = 0; i < lines.length; i++) {
        await editor.type(lines[i]);
        if (i < lines.length - 1) {
          await this.page.keyboard.press('Enter');
        }
      }

      await this.log('Post content entered');

      if (this.config.dryRun) {
        await this.log('DRY_RUN mode: Skipping actual post submission');
        await this.page.waitForTimeout(2000);

        // Close the post dialog
        const closeButton = await this.page.$('[data-test-id="close-button"], button[aria-label="Dismiss"]');
        if (closeButton) {
          await closeButton.click();
        }

        return { success: true, dryRun: true };
      }

      // Click the Post button
      await this.log('Submitting post...');
      const postButton = await this.page.waitForSelector('[data-test-id="share-box-post-button"], button[aria-label*="Post"]', {
        timeout: 5000
      });
      await postButton.click();

      // Wait for post to be submitted
      await this.page.waitForTimeout(3000);

      await this.log('Post submitted successfully!');
      return { success: true, dryRun: false };

    } catch (error) {
      await this.log(`Error posting to LinkedIn: ${error.message}`);
      throw error;
    }
  }

  async closeBrowser() {
    if (this.context) {
      await this.log('Closing browser...');
      await this.context.close();
    }
  }

  async archivePostedDraft(draft) {
    try {
      const timestamp = Date.now();
      const archivedFilename = `posted_${timestamp}_${draft.filename}`;
      const archivedPath = path.join(this.config.postedDir, archivedFilename);

      // Move to posted directory
      await fs.rename(draft.filepath, archivedPath);
      await this.log(`Draft archived: ${archivedFilename}`);

    } catch (error) {
      await this.log(`Error archiving draft: ${error.message}`);
    }
  }

  async processApprovedPosts() {
    try {
      await this.log('Checking for approved posts...');

      const approvedDrafts = await this.getPendingApprovals();

      if (approvedDrafts.length === 0) {
        await this.log('No approved posts found');
        return;
      }

      await this.log(`Found ${approvedDrafts.length} approved post(s)`);

      await this.launchBrowser();
      await this.navigateToLinkedIn();
      await this.waitForLinkedInLoad();

      for (const draft of approvedDrafts) {
        try {
          await this.log(`Processing: ${draft.filename}`);

          const postContent = this.extractPostContent(draft.content);
          const result = await this.postToLinkedIn(postContent);

          if (result.success) {
            if (result.dryRun) {
              await this.log(`DRY_RUN: Post would have been published`);
            } else {
              await this.log(`Post published successfully`);
            }

            await this.archivePostedDraft(draft);
          }

          // Wait between posts
          await this.page.waitForTimeout(5000);

        } catch (error) {
          await this.log(`Failed to post ${draft.filename}: ${error.message}`);
        }
      }

    } catch (error) {
      await this.log(`Error processing approved posts: ${error.message}`);
      throw error;
    } finally {
      await this.closeBrowser();
    }
  }

  async run(mode = 'process', options = {}) {
    try {
      await this.initialize();

      if (mode === 'generate') {
        // Generate a new draft
        const topic = options.topic || 'Business Update';
        const keyPoints = options.keyPoints || [];

        const postContent = await this.generatePost(topic, keyPoints);
        const draft = await this.createDraft(postContent, { topic });

        await this.log(`Draft created and ready for approval: ${draft.filename}`);
        return draft;

      } else if (mode === 'process') {
        // Process approved posts
        await this.processApprovedPosts();
      }

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
      handbookPath: config.paths.handbookPath,
      pendingApprovalDir: path.join(__dirname, config.paths.pendingApprovalDir),
      postedDir: path.join(__dirname, config.paths.postedDir),
      logsDir: path.join(__dirname, config.paths.logsDir),
      userDataDir: path.join(__dirname, config.paths.userDataDir),
      dryRun: config.dryRun,
      headless: config.browser.headless,
      viewport: config.browser.viewport
    };
  } catch (error) {
    console.error('Failed to load config.json, using defaults:', error.message);
    return {
      handbookPath: '../../Company_Handbook.md',
      pendingApprovalDir: path.join(__dirname, '../../Pending_Approval'),
      postedDir: path.join(__dirname, '../../Posted'),
      logsDir: path.join(__dirname, '../../Logs'),
      userDataDir: path.join(__dirname, 'linkedin_session'),
      dryRun: false
    };
  }
}

// Main execution
if (require.main === module) {
  const config = loadConfig();
  const skill = new LinkedInPostSkill(config);

  // Check command line arguments
  const args = process.argv.slice(2);
  const mode = args[0] || 'process';

  if (mode === 'generate') {
    const topic = args[1] || 'Business Update';
    const keyPoints = args.slice(2);

    skill.run('generate', { topic, keyPoints }).catch(console.error);
  } else {
    skill.run('process').catch(console.error);
  }
}

module.exports = LinkedInPostSkill;
