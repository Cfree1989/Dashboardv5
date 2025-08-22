FROM node:18-alpine

# Install curl for health checks
RUN apk add --no-cache curl

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies (cached until package.json changes)
RUN npm ci --only=production && npm cache clean --force

# Copy application code (changes frequently, so copied last)
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# Start the application in development mode
CMD ["npm", "run", "dev"] 