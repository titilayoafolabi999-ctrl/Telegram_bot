const mongoose = require('mongoose');
const config = require('../config/config');

const connectDatabase = async () => {
  try {
    await mongoose.connect(config.database.mongoUri);
    console.log('✅ MongoDB connected successfully');
  } catch (error) {
    console.error('❌ MongoDB connection failed:', error);
    process.exit(1);
  }
};

module.exports = { connectDatabase };
