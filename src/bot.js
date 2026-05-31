require('dotenv').config();
const { Telegraf } = require('telegraf');
const express = require('express');
const config = require('./config/config');
const googleDrive = require('./utils/googleDrive');

// Import commands
const { startCommand } = require('./commands/start');
const { chatCommand } = require('./commands/chat');
const { jokeCommand, countryCommand, translateCommand, exchangeCommand } = require('./commands/utilities');
const { profileCommand } = require('./commands/profile');
const { helpCommand } = require('./commands/help');

// Initialize bot and express server
const bot = new Telegraf(config.telegram.token);
const app = express();

// Middleware
app.use(express.json());

// Google OAuth2 callback endpoint
app.get('/api/v1/gdrive/callback', async (req, res) => {
  try {
    const { code, state } = req.query;
    const userId = state; // User ID passed as state parameter

    if (!code) {
      return res.status(400).send('❌ Authorization code not provided');
    }

    // Exchange code for token
    const tokens = await googleDrive.exchangeCodeForToken(code, userId);

    if (!tokens) {
      return res.status(500).send('❌ Failed to exchange code for token');
    }

    // Send success message
    res.send(`
      <html>
        <head>
          <title>✅ Authorization Successful</title>
          <style>
            body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { text-align: center; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); max-width: 500px; }
            h1 { color: #667eea; margin: 0 0 10px 0; }
            p { color: #666; margin: 10px 0; line-height: 1.6; }
            .code { background: #f0f0f0; padding: 10px; border-radius: 5px; font-family: monospace; margin-top: 20px; word-break: break-all; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>✅ Authorization Successful!</h1>
            <p>Your Google Drive has been connected to the Telegram bot.</p>
            <p>You can now go back to Telegram and use the bot commands.</p>
            <p><strong>Use /start to begin!</strong></p>
          </div>
        </body>
      </html>
    `);
  } catch (error) {
    console.error('❌ OAuth callback error:', error);
    res.status(500).send('❌ An error occurred during authorization');
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: '✅ ok' });
});

// Bot middleware - Logging
bot.use((ctx, next) => {
  const userInfo = `${ctx.from.first_name} (${ctx.from.id})`;
  const command = ctx.message?.text || 'action';
  console.log(`[${new Date().toISOString()}] ${userInfo} executed: ${command}`);
  return next();
});

// Command handlers
bot.command('start', startCommand);
bot.command('chat', chatCommand);
bot.command('joke', jokeCommand);
bot.command('country', countryCommand);
bot.command('translate', translateCommand);
bot.command('exchange', exchangeCommand);
bot.command('profile', profileCommand);
bot.command('help', helpCommand);

// Error handling
bot.catch((err, ctx) => {
  console.error('❌ Bot error:', err);
  ctx.reply('❌ An unexpected error occurred. Please try again.').catch(() => {});
});

// Graceful shutdown
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

// Start bot
const startBot = async () => {
  try {
    console.log('🚀 Starting Telegram Bot...');
    
    // Initialize Google Drive OAuth
    googleDrive.initializeOAuth();
    console.log('✅ Google Drive OAuth initialized');

    // Start Express server
    const PORT = config.port || 3000;
    app.listen(PORT, () => {
      console.log(`✅ Express server running on port ${PORT}`);
    });

    // Launch bot
    await bot.launch();
    console.log('✅ Bot is running!');
    console.log('📡 Bot will now listen for updates...');
  } catch (error) {
    console.error('❌ Failed to start bot:', error);
    process.exit(1);
  }
};

startBot();
