const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  telegramId: {
    type: String,
    unique: true,
    required: true,
  },
  username: String,
  firstName: String,
  lastName: String,
  xp: {
    type: Number,
    default: 0,
  },
  level: {
    type: Number,
    default: 1,
  },
  totalPoints: {
    type: Number,
    default: 0,
  },
  achievements: [String],
  dailyChallengesCompleted: {
    type: Number,
    default: 0,
  },
  newsPreferences: [String],
  lastDailyBriefing: Date,
  createdAt: {
    type: Date,
    default: Date.now,
  },
  updatedAt: {
    type: Date,
    default: Date.now,
  },
});

userSchema.pre('save', function (next) {
  this.updatedAt = Date.now();
  next();
});

module.exports = mongoose.model('User', userSchema);
