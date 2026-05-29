const aiChat = require('../modules/aiChat');
const googleDrive = require('../utils/googleDrive');

const chatCommand = async (ctx) => {
  try {
    const message = ctx.message.text.replace('/chat ', '').trim();

    if (!message) {
      await ctx.reply('📝 Usage: /chat <your message>');
      return;
    }

    await ctx.reply('⏳ Thinking...');

    const telegramId = ctx.from.id.toString();
    const userData = await googleDrive.getUserData(telegramId);

    if (!userData) {
      await ctx.reply('❌ User not found. Please use /start first.');
      return;
    }

    const conversationHistory = userData.conversationHistory || [];
    const response = await aiChat.chat(message, conversationHistory);

    if (response.error) {
      await ctx.reply(response.reply);
      return;
    }

    // Update conversation history
    userData.conversationHistory.push({ role: 'user', content: message });
    userData.conversationHistory.push({ role: 'assistant', content: response.reply });
    userData.messageCount = (userData.messageCount || 0) + 1;

    // Keep only last 10 messages
    if (userData.conversationHistory.length > 20) {
      userData.conversationHistory = userData.conversationHistory.slice(-20);
    }

    await googleDrive.saveUserData(telegramId, userData);

    // Split long responses
    const chunks = response.reply.match(/[\s\S]{1,4096}/g) || [response.reply];
    for (const chunk of chunks) {
      await ctx.reply(chunk, { parse_mode: 'Markdown' });
    }
  } catch (error) {
    console.error('Error in chat command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

module.exports = { chatCommand };
