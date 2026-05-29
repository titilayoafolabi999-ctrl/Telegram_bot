const newsManager = require('../modules/news');
const gamificationManager = require('../modules/gamification');

const newsCommand = async (ctx) => {
  try {
    await ctx.reply('📰 Fetching trending news...');

    const articles = await newsManager.getTopHeadlines('us', 'general');

    if (articles.length === 0) {
      await ctx.reply('❌ No news found. Please try again later.');
      return;
    }

    for (let i = 0; i < Math.min(3, articles.length); i++) {
      const formatted = newsManager.formatArticle(articles[i]);
      await ctx.reply(formatted, { parse_mode: 'Markdown' });
    }

    // Add XP for reading news
    const userId = ctx.from.id.toString();
    await gamificationManager.addXP(userId, 10, 'news_read');

    await ctx.reply('✅ News loaded! +10 XP earned');
  } catch (error) {
    console.error('Error in news command:', error);
    await ctx.reply('❌ An error occurred while fetching news.');
  }
};

const searchCommand = async (ctx) => {
  try {
    const query = ctx.message.text.replace('/search ', '').trim();

    if (!query) {
      await ctx.reply('📌 Usage: /search <topic>\nExample: /search technology');
      return;
    }

    await ctx.reply(`🔍 Searching for "${query}"...`);

    const articles = await newsManager.searchNews(query);

    if (articles.length === 0) {
      await ctx.reply(`❌ No articles found for "${query}"`);
      return;
    }

    for (let i = 0; i < Math.min(3, articles.length); i++) {
      const formatted = newsManager.formatArticle(articles[i]);
      await ctx.reply(formatted, { parse_mode: 'Markdown' });
    }

    // Add XP for searching
    const userId = ctx.from.id.toString();
    await gamificationManager.addXP(userId, 15, 'news_search');

    await ctx.reply(`✅ Found ${articles.length} articles! +15 XP earned`);
  } catch (error) {
    console.error('Error in search command:', error);
    await ctx.reply('❌ An error occurred while searching news.');
  }
};

const trendingCommand = async (ctx) => {
  try {
    await ctx.reply('📊 Fetching trending topics...');

    const topics = await newsManager.getTrendingTopics();

    if (topics.length === 0) {
      await ctx.reply('❌ No trending topics found.');
      return;
    }

    let message = '🔥 *Trending Topics*\n\n';
    topics.slice(0, 5).forEach((topic, index) => {
      message += `${index + 1}. ${topic.title}\n`;
      message += `   Source: ${topic.source}\n`;
      message += `   [Read More](${topic.url})\n\n`;
    });

    await ctx.reply(message, { parse_mode: 'Markdown' });

    // Add XP
    const userId = ctx.from.id.toString();
    await gamificationManager.addXP(userId, 10, 'trending_read');
  } catch (error) {
    console.error('Error in trending command:', error);
    await ctx.reply('❌ An error occurred while fetching trending topics.');
  }
};

module.exports = {
  newsCommand,
  searchCommand,
  trendingCommand,
};
