# For Damien's Personal Homelab - Dockerfile for K8S
# Notes for Damien - make sure you configure your DNS settings for your servers
# to point to in-house DNS server.
FROM nexus-dockerproxy.dsb-hub.local/node:18-alpine AS builder

# Set the working directory
WORKDIR /app

# Configure npm to use your Nexus registry
RUN npm config set strict-ssl false
RUN npm config set registry https://nexus.dsb-hub.local/repository/npm-proxy/

# Copy package.json
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the website (assuming you are using Docusaurus or similar)
RUN npm run build

# Step 2: Serve the website using Nginx
FROM nexus-dockerproxy.dsb-hub.local/nginx:alpine

# Copy the compiled website from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
