require('dotenv').config();

module.exports = {
  telegram: {
    token: process.env.TELEGRAM_BOT_TOKEN,
    username: process.env.BOT_USERNAME,
  },
  database: {
    mongoUri: process.env.MONGODB_URI || 'mongodb://localhost:27017/telegram_bot',
    redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  },
  api: {
    newsApiKey: process.env.NEWS_API_KEY,
  },
  environment: process.env.NODE_ENV || 'development',
};
