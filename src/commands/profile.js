const googleDrive = require('../utils/googleDrive');

const profileCommand = async (ctx) => {
  try {
    const telegramId = ctx.from.id.toString();
    const userData = await googleDrive.getUserData(telegramId);

    if (!userData) {
      await ctx.reply('❌ User not found. Please use /start first.');
      return;
    }

    const createdDate = new Date(userData.createdAt).toLocaleDateString();
    const message = `
👤 *Your Profile*

👤 Name: ${userData.firstName || 'Unknown'}
📱 Username: @${userData.username || 'N/A'}
💬 Messages: ${userData.messageCount || 0}
🗣️ Language: ${userData.preferences?.language || 'English'}
📅 Member Since: ${createdDate}
🆔 User ID: ${telegramId}
    `;

    await ctx.reply(message, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in profile command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

module.exports = { profileCommand };
