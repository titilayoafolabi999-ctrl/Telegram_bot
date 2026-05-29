const { Telegraf } = require('telegraf');
const config = require('./config/config');
const { connectDatabase } = require('./utils/database');

// Import commands
const { startCommand } = require('./commands/start');
const { profileCommand, leaderboardCommand, dailyCommand, achievementsCommand } = require('./commands/gamification');
const { newsCommand, searchCommand, trendingCommand } = require('./commands/news');
const { helpCommand } = require('./commands/help');

// Initialize bot
const bot = new Telegraf(config.telegram.token);

// Middleware
bot.use((ctx, next) => {
  console.log(`[${new Date().toISOString()}] ${ctx.from.first_name} (${ctx.from.id}) executed: ${ctx.message?.text || 'action'}`);
  return next();
});

// Command handlers
bot.command('start', startCommand);
bot.command('profile', profileCommand);
bot.command('leaderboard', leaderboardCommand);
bot.command('daily', dailyCommand);
bot.command('achievements', achievementsCommand);
bot.command('news', newsCommand);
bot.command('trending', trendingCommand);
bot.command('help', helpCommand);

// Search command with argument
bot.command('search', searchCommand);

// Error handling
bot.catch((err, ctx) => {
  console.error('Error:', err);
  ctx.reply('❌ An unexpected error occurred. Please try again.').catch(() => {});
});

// Start bot
const startBot = async () => {
  try {
    console.log('🚀 Starting Telegram Bot...');
    
    // Connect to MongoDB
    await connectDatabase();
    console.log('✅ Database connected');

    // Launch bot
    await bot.launch();
    console.log('✅ Bot is running!');

    // Enable graceful stop
    process.once('SIGINT', () => bot.stop('SIGINT'));
    process.once('SIGTERM', () => bot.stop('SIGTERM'));
  } catch (error) {
    console.error('❌ Failed to start bot:', error);
    process.exit(1);
  }
};

startBot();
