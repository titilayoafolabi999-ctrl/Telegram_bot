FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Expose port (if needed for future expansion)
EXPOSE 3000

# Start bot
CMD ["npm", "start"]
