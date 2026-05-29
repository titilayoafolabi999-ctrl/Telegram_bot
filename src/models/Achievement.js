const mongoose = require('mongoose');

const achievementSchema = new mongoose.Schema({
  userId: {
    type: String,
    required: true,
  },
  achievementName: {
    type: String,
    required: true,
  },
  description: String,
  icon: String,
  points: {
    type: Number,
    default: 10,
  },
  unlockedAt: {
    type: Date,
    default: Date.now,
  },
});

module.exports = mongoose.model('Achievement', achievementSchema);
