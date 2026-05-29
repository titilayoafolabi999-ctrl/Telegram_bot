const User = require('../models/User');

const startCommand = async (ctx) => {
  try {
    const { id, username, first_name, last_name } = ctx.from;

    // Check if user exists, if not create
    let user = await User.findOne({ telegramId: id.toString() });
    if (!user) {
      user = new User({
        telegramId: id.toString(),
        username: username || 'Anonymous',
        firstName: first_name,
        lastName: last_name,
      });
      await user.save();
    }

    const welcomeMessage = `
🎮 Welcome to the Lightning Bot! ⚡

I'm a productive bot built with Node.js, packed with amazing features:

✨ *Features:*
🎮 Gamification - Earn XP, level up, unlock achievements
📰 News - Get trending news and stay informed
⚡ Lightning Fast - Quick and responsive commands
🏆 Leaderboards - Compete with other users
🎯 Daily Challenges - Complete tasks and earn rewards

*Available Commands:*
/start - Show this message
/profile - View your stats
/leaderboard - See top players
/news - Get trending news
/search <topic> - Search news
/daily - Complete daily challenge
/achievements - View your achievements
/help - Get help

Let's get started! 🚀
    `;

    await ctx.reply(welcomeMessage, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in start command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

module.exports = { startCommand };
