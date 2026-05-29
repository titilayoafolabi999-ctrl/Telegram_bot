const { google } = require('googleapis');
const config = require('../config/config');
const { v4: uuidv4 } = require('uuid');

class GoogleDriveManager {
  constructor() {
    this.drive = null;
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;

    try {
      const auth = new google.auth.GoogleAuth({
        credentials: {
          type: 'service_account',
          project_id: config.googleDrive.privateKey?.split('\n')[1],
          private_key_id: uuidv4(),
          private_key: config.googleDrive.privateKey,
          client_email: config.googleDrive.serviceAccountEmail,
          client_id: uuidv4(),
          auth_uri: 'https://accounts.google.com/o/oauth2/auth',
          token_uri: 'https://oauth2.googleapis.com/token',
          auth_provider_x509_cert_url: 'https://www.googleapis.com/oauth2/v1/certs',
        },
        scopes: ['https://www.googleapis.com/auth/drive'],
      });

      this.drive = google.drive({ version: 'v3', auth });
      this.initialized = true;
      console.log('✅ Google Drive initialized');
    } catch (error) {
      console.error('❌ Google Drive initialization failed:', error);
      this.initialized = false;
    }
  }

  async saveUserData(telegramId, data) {
    try {
      if (!this.initialized) await this.initialize();

      const fileName = `user_${telegramId}.json`;
      const fileContent = JSON.stringify(data, null, 2);

      // Check if file exists
      const query = `name='${fileName}' and '${config.googleDrive.folderId}' in parents and trashed=false`;
      const response = await this.drive.files.list({
        q: query,
        spaces: 'drive',
        pageSize: 1,
        fields: 'files(id)',
      });

      let fileId;

      if (response.data.files.length > 0) {
        // Update existing file
        fileId = response.data.files[0].id;
        await this.drive.files.update({
          fileId,
          media: {
            mimeType: 'application/json',
            body: fileContent,
          },
        });
      } else {
        // Create new file
        const fileMetadata = {
          name: fileName,
          mimeType: 'application/json',
          parents: [config.googleDrive.folderId],
        };
        const result = await this.drive.files.create({
          resource: fileMetadata,
          media: {
            mimeType: 'application/json',
            body: fileContent,
          },
          fields: 'id',
        });
        fileId = result.data.id;
      }

      console.log(`✅ User data saved for ${telegramId}`);
      return fileId;
    } catch (error) {
      console.error('❌ Error saving user data:', error);
      return null;
    }
  }

  async getUserData(telegramId) {
    try {
      if (!this.initialized) await this.initialize();

      const fileName = `user_${telegramId}.json`;
      const query = `name='${fileName}' and '${config.googleDrive.folderId}' in parents and trashed=false`;

      const response = await this.drive.files.list({
        q: query,
        spaces: 'drive',
        pageSize: 1,
        fields: 'files(id)',
      });

      if (response.data.files.length === 0) {
        return null;
      }

      const fileId = response.data.files[0].id;
      const fileContent = await this.drive.files.get({
        fileId,
        alt: 'media',
      });

      return fileContent.data;
    } catch (error) {
      console.error('❌ Error getting user data:', error);
      return null;
    }
  }

  async deleteUserData(telegramId) {
    try {
      if (!this.initialized) await this.initialize();

      const fileName = `user_${telegramId}.json`;
      const query = `name='${fileName}' and '${config.googleDrive.folderId}' in parents and trashed=false`;

      const response = await this.drive.files.list({
        q: query,
        spaces: 'drive',
        pageSize: 1,
        fields: 'files(id)',
      });

      if (response.data.files.length > 0) {
        const fileId = response.data.files[0].id;
        await this.drive.files.delete({ fileId });
        console.log(`✅ User data deleted for ${telegramId}`);
      }
    } catch (error) {
      console.error('❌ Error deleting user data:', error);
    }
  }
}

module.exports = new GoogleDriveManager();
