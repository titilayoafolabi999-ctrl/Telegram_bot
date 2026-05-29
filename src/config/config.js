require('dotenv').config();

module.exports = {
  telegram: {
    token: process.env.TELEGRAM_BOT_TOKEN,
    username: process.env.BOT_USERNAME,
  },
  googleDrive: {
    serviceAccountEmail: process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL,
    privateKey: process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
    folderId: process.env.GOOGLE_DRIVE_FOLDER_ID,
  },
  groq: {
    apiKey: process.env.GROQ_API_KEY,
  },
  environment: process.env.NODE_ENV || 'production',
  port: process.env.PORT || 3000,
};
