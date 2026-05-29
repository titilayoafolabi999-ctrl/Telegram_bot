# Telegram AI Assistant Bot 🤖

A productive Telegram bot with AI chat, translations, utilities, and Google Drive storage.

## Features ✨

- **🤖 AI Chat** - Powered by Groq API (free)
- **🌐 Translations** - Translate to any language
- **😄 Jokes** - Get random dad jokes
- **🌍 Country Info** - Learn about countries
- **💱 Currency Converter** - Real-time exchange rates
- **💾 Cloud Storage** - All data stored in Google Drive
- **🚀 Render Deployment** - Deploy on free tier

## Tech Stack

- **Node.js** - Runtime
- **Telegraf** - Telegram bot framework
- **Groq AI** - Free AI API
- **Google Drive API** - Cloud storage
- **REST APIs** - icanhazdadjoke, REST Countries, exchangerate-api

## Installation

```bash
# Clone repository
git clone <your-repo-url>
cd Telegram_bot

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Add your tokens to .env
# Then run
npm start
```

## Commands

| Command | Usage | Example |
|---------|-------|----------|
| /start | Initialize bot | /start |
| /chat | Chat with AI | /chat What is AI? |
| /translate | Translate text | /translate Spanish Hello |
| /joke | Get a random joke | /joke |
| /country | Get country info | /country France |
| /exchange | Convert currency | /exchange USD EUR 100 |
| /profile | View your profile | /profile |
| /help | Show help | /help |

## Deployment

### Render.com (Free)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

```bash
# Quick steps:
# 1. Get API keys (Groq, Telegram)
# 2. Set up Google Drive service account
# 3. Push to GitHub
# 4. Connect to Render
# 5. Add environment variables
# 6. Deploy!
```

## Free APIs

- **Groq** - mixtral-8x7b-32768 model (30 req/min free)
- **icanhazdadjoke.com** - Unlimited jokes
- **REST Countries** - Unlimited country data
- **exchangerate-api.com** - Limited free tier

## Configuration

### Google Drive Setup

1. Create Google Cloud project
2. Enable Drive API
3. Create service account
4. Download private key
5. Create folder in Drive
6. Share with service account

### Environment Variables

```env
TELEGRAM_BOT_TOKEN=<your-token>
GROQ_API_KEY=<your-groq-key>
GOOGLE_SERVICE_ACCOUNT_EMAIL=<service-account-email>
GOOGLE_PRIVATE_KEY=<private-key>
GOOGLE_DRIVE_FOLDER_ID=<folder-id>
NODE_ENV=production
```

## Storage

All user data is stored as JSON files in Google Drive:
- Conversation history
- User preferences
- Message count
- Profile information

## License

MIT

## Author

titilayoafolabi999
