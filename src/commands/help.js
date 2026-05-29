const helpCommand = async (ctx) => {
  const helpMessage = `
🤖 *Available Commands*

*AI & Chat:*
/chat <message> - Chat with AI
/translate <lang> <text> - Translate text

*Utilities:*
/joke - Get a random joke
/country <name> - Get country information
/exchange <from> <to> <amount> - Convert currency

*Account:*
/profile - View your profile
/start - Show welcome message
/help - Show this help message

*Examples:*
💬 /chat What is the capital of France?
🌐 /translate Spanish Hello world
😄 /joke
🌍 /country Japan
💱 /exchange USD EUR 100

*Tips:*
• Chat history is saved automatically
• Use /translate for any language
• Get real-time exchange rates
• Learn interesting facts about countries

Need more help? Just ask! 🚀
  `;

  await ctx.reply(helpMessage, { parse_mode: 'Markdown' });
};

module.exports = { helpCommand };
