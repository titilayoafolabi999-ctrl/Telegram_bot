require('dotenv').config();
const { Telegraf } = require('telegraf');
const config = require('./config/config');
const googleDrive = require('./utils/googleDrive');

// Import commands
const { startCommand } = require('./commands/start');
const { chatCommand } = require('./commands/chat');
const { jokeCommand, countryCommand, translateCommand, exchangeCommand } = require('./commands/utilities');
const { profileCommand } = require('./commands/profile');
const { helpCommand } = require('./commands/help');

// Initialize bot
const bot = new Telegraf(config.telegram.token);

// Middleware - Logging
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
    
    // Initialize Google Drive
    await googleDrive.initialize();
    console.log('✅ Google Drive initialized');

    // Launch bot
    await bot.launch();
    console.log('✅ Bot is running!');
    console.log(`📡 Bot will now listen for updates...`);
  } catch (error) {
    console.error('❌ Failed to start bot:', error);
    process.exit(1);
  }
};

startBot();
