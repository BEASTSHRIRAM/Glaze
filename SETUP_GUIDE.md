# Glaze Setup Guide - Getting API Credentials

This guide will walk you through obtaining all the necessary API credentials for Glaze.

## Prerequisites

- A Google account
- Access to Google Cloud Console
- Access to Google AI Studio

---

## Part 1: Google OAuth Client ID & Secret

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top (next to "Google Cloud")
3. Click **"New Project"**
4. Enter project name: `Glaze` (or any name you prefer)
5. Click **"Create"**
6. Wait for the project to be created (you'll see a notification)

### Step 2: Enable Google Drive API

1. Make sure your new project is selected (check the top bar)
2. Go to **"APIs & Services"** > **"Library"** (from the left sidebar)
3. Search for **"Google Drive API"**
4. Click on **"Google Drive API"**
5. Click **"Enable"**
6. Wait for it to enable (takes a few seconds)

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** > **"OAuth consent screen"** (left sidebar)
2. Select **"External"** (unless you have a Google Workspace account)
3. Click **"Create"**

**Fill in the required fields:**
- **App name**: `Glaze`
- **User support email**: Your email address
- **App logo**: (Optional) Upload the Glaze logo if you want
- **Developer contact information**: Your email address

4. Click **"Save and Continue"**

**Scopes page:**
5. Click **"Add or Remove Scopes"**
6. Search and select these scopes:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/userinfo.email`
7. Click **"Update"**
8. Click **"Save and Continue"**

**Test users page:**
9. Click **"Add Users"**
10. Add your Google email address (the one you'll use to test)
11. Click **"Add"**
12. Click **"Save and Continue"**

13. Review the summary and click **"Back to Dashboard"**

### Step 4: Create OAuth Credentials

1. Go to **"APIs & Services"** > **"Credentials"** (left sidebar)
2. Click **"Create Credentials"** at the top
3. Select **"OAuth client ID"**

**Configure the OAuth client:**
4. **Application type**: Select **"Web application"**
5. **Name**: `Glaze Backend`

**Authorized redirect URIs:**
6. Click **"Add URI"**
7. Enter: `http://localhost:8000/auth/callback`
8. Click **"Add URI"** again
9. Enter: `http://127.0.0.1:8000/auth/callback`

10. Click **"Create"**

### Step 5: Copy Your Credentials

A popup will appear with your credentials:

- **Client ID**: Something like `123456789-abcdefg.apps.googleusercontent.com`
- **Client Secret**: Something like `GOCSPX-abcdefghijklmnop`

**⚠️ IMPORTANT**: Copy both of these and save them securely!

You can also download the JSON file for backup.

If you close the popup, you can always find them again:
- Go to **"Credentials"** page
- Click on your OAuth client name
- Your Client ID and Secret will be displayed

---

## Part 2: Google Gemini API Key

### Step 1: Go to Google AI Studio

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account

### Step 2: Create API Key

1. Click **"Get API Key"** or **"Create API Key"**
2. Select **"Create API key in new project"** (or select your existing Glaze project)
3. Click **"Create API key in new project"**

### Step 3: Copy Your API Key

- Your API key will be displayed (looks like: `AIzaSyABC123...`)
- **⚠️ IMPORTANT**: Copy this key and save it securely!
- Click **"Copy"** to copy it to clipboard

**Note**: Keep this key private. Don't share it or commit it to version control.

---

## Part 3: Configure Your Glaze Backend

### Step 1: Create .env File

1. Navigate to your `backend` directory
2. Copy the example file:
   ```bash
   cd backend
   cp .env.example .env
   ```

### Step 2: Edit .env File

Open `backend/.env` in a text editor and fill in your credentials:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Google Gemini API
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# Qdrant Configuration (defaults are fine)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Backend Configuration (defaults are fine)
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=development

# Security (generate a random secret key)
SECRET_KEY=your_random_secret_key_here_change_this
```

### Step 3: Generate a Secret Key

For the `SECRET_KEY`, generate a random string. You can use:

**Python:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**PowerShell:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Or use any random string generator online** (at least 32 characters)

### Step 4: Save the File

Save your `.env` file with all the credentials filled in.

**⚠️ SECURITY NOTE**: 
- Never commit `.env` to git (it's already in `.gitignore`)
- Keep your credentials private
- Don't share your API keys

---

## Part 4: Verify Your Setup

### Test Backend Connection

1. Start your backend:
   ```bash
   cd backend
   python main.py
   ```

2. Open browser and go to: `http://localhost:8000/health`
3. You should see a JSON response with status "healthy"

### Test OAuth Flow

1. Load the Chrome Extension
2. Click the Glaze icon
3. Click "Sign in with Google"
4. You should be redirected to Google's consent screen
5. Authorize the app
6. You should be redirected back and logged in

---

## Troubleshooting

### "Redirect URI mismatch" Error

**Problem**: OAuth redirect URI doesn't match

**Solution**:
1. Go to Google Cloud Console > Credentials
2. Click on your OAuth client
3. Make sure these URIs are added:
   - `http://localhost:8000/auth/callback`
   - `http://127.0.0.1:8000/auth/callback`

### "Access blocked: This app's request is invalid"

**Problem**: OAuth consent screen not configured properly

**Solution**:
1. Go to OAuth consent screen
2. Make sure you added your email as a test user
3. Make sure the required scopes are added

### "Invalid API Key" for Gemini

**Problem**: Gemini API key is incorrect or not activated

**Solution**:
1. Go back to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Verify your API key
3. Make sure you copied it correctly (no extra spaces)
4. Try creating a new API key if needed

### "Cannot connect to Qdrant"

**Problem**: Qdrant is not running

**Solution**:
```bash
docker-compose up -d qdrant
```

---

## API Quotas and Limits

### Google Drive API
- **Free tier**: 1,000 requests per 100 seconds per user
- Should be sufficient for personal use

### Gemini API
- **Free tier**: 15 requests per minute
- 1,500 requests per day
- Sufficient for indexing ~100-200 files per day

### Qdrant
- **Self-hosted**: No limits (runs on your machine)

---

## Next Steps

Once you have all credentials configured:

1. ✅ Start Qdrant: `docker-compose up -d qdrant`
2. ✅ Start Backend: `cd backend && python main.py`
3. ✅ Load Chrome Extension
4. ✅ Sign in with Google
5. ✅ Start indexing your Drive files
6. ✅ Search with natural language!

---

## Need Help?

If you encounter any issues:

1. Check the backend logs for error messages
2. Verify all credentials are correct in `.env`
3. Make sure all services are running (Qdrant, Backend)
4. Check the browser console for extension errors

For more help, refer to the main [README.md](README.md) file.
