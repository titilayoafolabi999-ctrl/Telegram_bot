const gamificationManager = require('../modules/gamification');
const User = require('../models/User');

const profileCommand = async (ctx) => {
  try {
    const userId = ctx.from.id.toString();
    const stats = await gamificationManager.getUserStats(userId);

    if (!stats) {
      await ctx.reply('❌ User profile not found. Please use /start first.');
      return;
    }

    const message = `
👤 *Your Profile*

Username: ${stats.username}
Level: ${stats.level} 🎮
XP: ${stats.xp}
Total Points: ${stats.totalPoints} ⭐
Achievements: ${stats.achievements.length}
Daily Challenges: ${stats.dailyChallengesCompleted}

${stats.achievements.length > 0 ? `\n🏅 *Achievements:*\n${stats.achievements.join('\n')}` : ''}
    `;

    await ctx.reply(message, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in profile command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

const leaderboardCommand = async (ctx) => {
  try {
    const leaderboard = await gamificationManager.getLeaderboard(10);

    if (leaderboard.length === 0) {
      await ctx.reply('📊 Leaderboard is empty. Be the first!');
      return;
    }

    let message = '🏆 *Top 10 Leaderboard*\n\n';
    leaderboard.forEach((user, index) => {
      message += `${index + 1}. ${user.firstName || user.username}\n`;
      message += `   Level: ${user.level} | Points: ${user.totalPoints}\n\n`;
    });

    await ctx.reply(message, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in leaderboard command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

const dailyCommand = async (ctx) => {
  try {
    const userId = ctx.from.id.toString();
    const user = await User.findOne({ telegramId: userId });

    if (!user) {
      await ctx.reply('❌ User not found. Please use /start first.');
      return;
    }

    const today = new Date().toDateString();
    const lastBriefing = user.lastDailyBriefing ? new Date(user.lastDailyBriefing).toDateString() : null;

    if (lastBriefing === today) {
      await ctx.reply('⏰ You already completed today\'s challenge! Come back tomorrow.');
      return;
    }

    await gamificationManager.completeDailyChallenge(userId);
    user.lastDailyBriefing = new Date();
    await user.save();

    await ctx.reply('✅ Daily challenge completed!\n+50 XP earned 🌟');
  } catch (error) {
    console.error('Error in daily command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

const achievementsCommand = async (ctx) => {
  try {
    const userId = ctx.from.id.toString();
    const stats = await gamificationManager.getUserStats(userId);

    if (!stats) {
      await ctx.reply('❌ User not found. Please use /start first.');
      return;
    }

    if (stats.achievements.length === 0) {
      await ctx.reply('🏅 You haven\'t unlocked any achievements yet. Keep playing!');
      return;
    }

    let message = '🏅 *Your Achievements*\n\n';
    stats.achievements.forEach((achievement) => {
      message += `✨ ${achievement}\n`;
    });

    await ctx.reply(message, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in achievements command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

module.exports = {
  profileCommand,
  leaderboardCommand,
  dailyCommand,
  achievementsCommand,
};
