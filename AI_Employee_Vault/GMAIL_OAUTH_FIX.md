## Gmail OAuth Setup - Add Test User

Your Gmail API app "hackathon-0" is in testing mode and needs your email added as a test user.

### Steps to Fix:

1. **Go to Google Cloud Console:**
   https://console.cloud.google.com/apis/credentials/consent?project=ai-employee-488021

2. **Click "OAuth consent screen" in the left sidebar** (if not already there)

3. **Scroll down to "Test users" section**

4. **Click "+ ADD USERS"**

5. **Enter your Gmail address** (the one you're trying to authenticate with)

6. **Click "SAVE"**

7. **Try authentication again:**
   ```bash
   bash authenticate_gmail_manual.sh
   ```

### Alternative: Use the Account That Created the Project

If you don't have access to add test users, try authenticating with the Google account that created the "ai-employee-488021" project. That account is automatically authorized.

### If You Don't Have Access to Google Cloud Console:

You'll need to either:
- Ask the project owner to add your email as a test user
- Or create your own Gmail API credentials:
  1. Go to https://console.cloud.google.com/
  2. Create a new project
  3. Enable Gmail API
  4. Create OAuth 2.0 credentials
  5. Download credentials.json
  6. Replace the existing credentials.json file

---

**Quick Link to Your Project:**
https://console.cloud.google.com/apis/credentials/consent?project=ai-employee-488021

**Project ID:** ai-employee-488021
**App Name:** hackathon-0
