const googleDrive = require('../utils/googleDrive');
const User = require('../models/User');

const startCommand = async (ctx) => {
  try {
    const { id, username, first_name, last_name } = ctx.from;
    const telegramId = id.toString();

    // Initialize Google Drive
    await googleDrive.initialize();

    // Check if user exists
    let userData = await googleDrive.getUserData(telegramId);
    if (!userData) {
      userData = {
        telegramId,
        username: username || 'Anonymous',
        firstName: first_name,
        lastName: last_name,
        conversationHistory: [],
        messageCount: 0,
        createdAt: new Date().toISOString(),
        preferences: {
          language: 'English',
        },
      };
      await googleDrive.saveUserData(telegramId, userData);
    }

    const welcomeMessage = `
🤖 *Welcome to AI Assistant Bot!* 🚀

I'm a productive bot with amazing features:

✨ *Features:*
💬 AI Chat - Chat with me using Groq AI
🌍 Translations - Translate text to any language
😄 Jokes - Get random jokes
🌐 Country Info - Learn about countries
💱 Currency Converter - Real-time exchange rates

*Available Commands:*
/start - Show this message
/chat <message> - Chat with AI
/translate <language> <text> - Translate text
/joke - Get a random joke
/country <name> - Get country info
/exchange <from> <to> <amount> - Currency conversion
/help - Get help
/profile - View your profile

*How to use:*
1️⃣ Type /chat followed by your question
2️⃣ Use /translate to convert languages
3️⃣ Have fun with jokes and country facts!

Let's get started! 🎉
    `;

    await ctx.reply(welcomeMessage, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error in start command:', error);
    await ctx.reply('❌ An error occurred. Please try again.');
  }
};

module.exports = { startCommand };
