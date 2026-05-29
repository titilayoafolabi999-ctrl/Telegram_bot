const axios = require('axios');
const config = require('../config/config');

class AIChatManager {
  constructor() {
    this.groqApiUrl = 'https://api.groq.com/openai/v1/chat/completions';
    this.apiKey = config.groq.apiKey;
  }

  async chat(message, conversationHistory = []) {
    try {
      const messages = [
        ...conversationHistory,
        { role: 'user', content: message },
      ];

      const response = await axios.post(this.groqApiUrl, {
        model: 'mixtral-8x7b-32768',
        messages,
        temperature: 0.7,
        max_tokens: 1024,
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      const reply = response.data.choices[0].message.content;
      return {
        reply,
        role: 'assistant',
      };
    } catch (error) {
      console.error('❌ Groq API error:', error.response?.data || error.message);
      return {
        reply: '❌ Sorry, I couldn\'t process your request. Please try again.',
        error: true,
      };
    }
  }

  async translate(text, targetLanguage) {
    try {
      const message = `Translate the following text to ${targetLanguage}. Only provide the translation, nothing else:\n\n${text}`;
      const response = await axios.post(this.groqApiUrl, {
        model: 'mixtral-8x7b-32768',
        messages: [{ role: 'user', content: message }],
        temperature: 0.3,
        max_tokens: 512,
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      const translation = response.data.choices[0].message.content;
      return translation;
    } catch (error) {
      console.error('❌ Translation error:', error.message);
      return null;
    }
  }
}

module.exports = new AIChatManager();
