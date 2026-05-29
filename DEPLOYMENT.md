# Deployment Guide for Render.com

## Prerequisites

1. **Telegram Bot Token** - Get from [@BotFather](https://t.me/botfather)
2. **Groq API Key** - Sign up at [console.groq.com](https://console.groq.com) (Free tier available)
3. **Google Drive Setup**:
   - Create a Google Cloud project
   - Enable Google Drive API
   - Create a service account
   - Download the private key JSON
   - Create a folder in Google Drive
   - Share it with the service account email

## Step-by-Step Deployment

### 1. Prepare Google Drive
```bash
# Create a service account:
# 1. Go to Google Cloud Console
# 2. Create a new project
# 3. Enable Google Drive API
# 4. Create service account
# 5. Generate private key (JSON)
# 6. Create a folder in Google Drive
# 7. Share folder with service account email
```

### 2. Get Groq API Key
```bash
# Go to https://console.groq.com
# Sign up for free
# Generate API key
```

### 3. Deploy to Render
```bash
# 1. Push code to GitHub
git push origin main

# 2. Go to https://render.com
# 3. Click "New" > "Web Service"
# 4. Connect your GitHub repository
# 5. Fill in the details:
#    - Name: telegram-bot
#    - Runtime: Node
#    - Build Command: npm install
#    - Start Command: npm start
#    - Plan: Free

# 6. Add environment variables:
#    - TELEGRAM_BOT_TOKEN: your_token
#    - GROQ_API_KEY: your_groq_key
#    - GOOGLE_SERVICE_ACCOUNT_EMAIL: your_service_account_email
#    - GOOGLE_PRIVATE_KEY: your_private_key (paste entire key with \n escape sequences)
#    - GOOGLE_DRIVE_FOLDER_ID: your_folder_id
#    - NODE_ENV: production
```

## Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_telegram_token
GROQ_API_KEY=your_groq_api_key
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service@project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
NODE_ENV=production
```

## Free APIs Used

1. **Groq AI** - Free tier includes 30 requests per minute
2. **icanhazdadjoke.com** - Free jokes API
3. **REST Countries** - Free country information API
4. **exchangerate-api.com** - Free currency conversion API

## Testing

After deployment:
```bash
# Find your bot on Telegram
/start - See welcome message
/chat What is AI? - Chat with AI
/joke - Get a random joke
/country France - Get country info
/exchange USD EUR 100 - Convert currency
/translate Spanish Hello - Translate text
```

## Troubleshooting

### Bot not responding
- Check Render logs
- Verify TELEGRAM_BOT_TOKEN is correct
- Ensure bot is running with `npm start`

### Google Drive errors
- Verify service account has access to folder
- Check folder ID is correct
- Ensure private key is properly escaped

### AI responses not working
- Verify GROQ_API_KEY is correct
- Check Groq API quota
- Ensure message is not too long

## Notes

- Render free tier may sleep after inactivity
- For always-on bot, upgrade to paid plan
- All user data is stored in Google Drive
- No database needed
