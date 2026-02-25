## How to Create Your Own Gmail API Credentials

If you don't have access to the existing Google Cloud project, follow these steps:

### Step 1: Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "NEW PROJECT"
3. Name it (e.g., "AI Employee Watcher")
4. Click "CREATE"

### Step 2: Enable Gmail API

1. Go to https://console.cloud.google.com/apis/library
2. Search for "Gmail API"
3. Click on it
4. Click "ENABLE"

### Step 3: Configure OAuth Consent Screen

1. Go to https://console.cloud.google.com/apis/credentials/consent
2. Select "External" user type
3. Click "CREATE"
4. Fill in:
   - App name: "AI Employee Watcher"
   - User support email: Your email
   - Developer contact: Your email
5. Click "SAVE AND CONTINUE"
6. On "Scopes" page, click "ADD OR REMOVE SCOPES"
7. Search for "gmail.readonly"
8. Check the box for ".../auth/gmail.readonly"
9. Click "UPDATE" → "SAVE AND CONTINUE"
10. On "Test users" page, click "+ ADD USERS"
11. Add your Gmail address
12. Click "SAVE AND CONTINUE"

### Step 4: Create OAuth Credentials

1. Go to https://console.cloud.google.com/apis/credentials
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "Gmail Watcher"
5. Click "CREATE"
6. Click "DOWNLOAD JSON"

### Step 5: Replace credentials.json

1. Rename the downloaded file to `credentials.json`
2. Replace the existing file:
   ```bash
   cp ~/Downloads/credentials.json /mnt/c/Users/"Tesla Laptops"/Desktop/AI_Employee_Vault/AI_Employee_Vault/credentials.json
   ```

### Step 6: Authenticate

```bash
bash authenticate_gmail_manual.sh
```

Now it will use your own credentials!
