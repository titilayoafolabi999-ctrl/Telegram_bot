// User model structure for Google Drive storage
// This represents the structure of user data stored in Google Drive

const userStructure = {
  telegramId: String,
  username: String,
  firstName: String,
  lastName: String,
  conversationHistory: Array, // Chat history
  messageCount: Number,
  createdAt: Date,
  updatedAt: Date,
  preferences: {
    language: String,
  },
};

module.exports = userStructure;
