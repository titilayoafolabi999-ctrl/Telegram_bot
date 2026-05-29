const User = require('../models/User');
const Achievement = require('../models/Achievement');

class GamificationManager {
  constructor() {
    this.xpPerAction = {
      command: 5,
      dailyChallenge: 50,
      newsShare: 10,
    };
    this.xpPerLevel = 100;
  }

  async addXP(telegramId, xpAmount, reason = 'action') {
    try {
      const user = await User.findOne({ telegramId });
      if (!user) return null;

      user.xp += xpAmount;
      user.totalPoints += xpAmount;

      // Check for level up
      const newLevel = Math.floor(user.xp / this.xpPerLevel) + 1;
      if (newLevel > user.level) {
        user.level = newLevel;
        await this.unlockAchievement(telegramId, `Level ${newLevel} Reached`);
      }

      await user.save();
      return user;
    } catch (error) {
      console.error('Error adding XP:', error);
      return null;
    }
  }

  async unlockAchievement(telegramId, achievementName) {
    try {
      const user = await User.findOne({ telegramId });
      if (!user) return null;

      if (user.achievements.includes(achievementName)) {
        return null; // Already unlocked
      }

      user.achievements.push(achievementName);
      await user.save();

      const achievement = new Achievement({
        userId: telegramId,
        achievementName,
        points: 20,
      });

      await achievement.save();
      return achievement;
    } catch (error) {
      console.error('Error unlocking achievement:', error);
      return null;
    }
  }

  async getLeaderboard(limit = 10) {
    try {
      const leaderboard = await User.find()
        .sort({ totalPoints: -1 })
        .limit(limit)
        .select('username firstName totalPoints level xp');

      return leaderboard;
    } catch (error) {
      console.error('Error getting leaderboard:', error);
      return [];
    }
  }

  async getUserStats(telegramId) {
    try {
      const user = await User.findOne({ telegramId });
      if (!user) return null;

      return {
        username: user.username,
        level: user.level,
        xp: user.xp,
        totalPoints: user.totalPoints,
        achievements: user.achievements,
        dailyChallengesCompleted: user.dailyChallengesCompleted,
      };
    } catch (error) {
      console.error('Error getting user stats:', error);
      return null;
    }
  }

  async completeDailyChallenge(telegramId) {
    try {
      const user = await User.findOne({ telegramId });
      if (!user) return null;

      user.dailyChallengesCompleted += 1;
      await this.addXP(telegramId, this.xpPerAction.dailyChallenge);

      if (user.dailyChallengesCompleted % 7 === 0) {
        await this.unlockAchievement(telegramId, `${user.dailyChallengesCompleted} Daily Challenges`);
      }

      await user.save();
      return user;
    } catch (error) {
      console.error('Error completing daily challenge:', error);
      return null;
    }
  }
}

module.exports = new GamificationManager();
