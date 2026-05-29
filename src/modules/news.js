const axios = require('axios');
const config = require('../config/config');

class NewsManager {
  constructor() {
    this.newsApiBaseUrl = 'https://newsapi.org/v2';
    this.apiKey = config.api.newsApiKey;
  }

  async getTopHeadlines(country = 'us', category = 'general') {
    try {
      const response = await axios.get(`${this.newsApiBaseUrl}/top-headlines`, {
        params: {
          country,
          category,
          apiKey: this.apiKey,
          pageSize: 5,
        },
      });

      return response.data.articles || [];
    } catch (error) {
      console.error('Error fetching headlines:', error.message);
      return [];
    }
  }

  async searchNews(query, sortBy = 'publishedAt') {
    try {
      const response = await axios.get(`${this.newsApiBaseUrl}/everything`, {
        params: {
          q: query,
          sortBy,
          apiKey: this.apiKey,
          pageSize: 5,
        },
      });

      return response.data.articles || [];
    } catch (error) {
      console.error('Error searching news:', error.message);
      return [];
    }
  }

  async getTrendingTopics() {
    try {
      const response = await axios.get(`${this.newsApiBaseUrl}/top-headlines`, {
        params: {
          country: 'us',
          apiKey: this.apiKey,
          pageSize: 10,
        },
      });

      const articles = response.data.articles || [];
      const topics = articles.map(article => ({
        title: article.title,
        source: article.source.name,
        url: article.url,
        image: article.urlToImage,
        publishedAt: article.publishedAt,
      }));

      return topics;
    } catch (error) {
      console.error('Error getting trending topics:', error.message);
      return [];
    }
  }

  formatArticle(article) {
    return `
📰 *${article.title}*
Source: ${article.source.name}
Published: ${new Date(article.publishedAt).toLocaleDateString()}

${article.description || 'No description available'}

[Read More](${article.url})
    `;
  }
}

module.exports = new NewsManager();
