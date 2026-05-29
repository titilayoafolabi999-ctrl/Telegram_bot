const helpCommand = async (ctx) => {
  const helpMessage = `
🤖 *Available Commands*

*Gamification:*
/profile - View your profile and stats
/leaderboard - See top 10 players
/daily - Complete daily challenge
/achievements - View your achievements

*News:*
/news - Get trending news
/search <topic> - Search for news on a topic
/trending - See trending topics

*Other:*
/start - Show welcome message
/help - Show this help message

*How it Works:*
✨ Earn XP by using commands
🎮 Level up and unlock achievements
📰 Read news and stay informed
🏆 Compete on the leaderboard

*Tips:*
• Complete daily challenges for bonus XP
• Search for topics you're interested in
• Check the leaderboard to see where you stand
• Unlock achievements to boost your score

Questions? Feel free to reach out! 💬
  `;

  await ctx.reply(helpMessage, { parse_mode: 'Markdown' });
};

module.exports = { helpCommand };
