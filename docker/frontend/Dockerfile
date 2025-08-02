# Use Node.js 20 with Debian Bullseye as the base image
FROM node:20-bullseye

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definition files first for better layer caching
COPY package.json package-lock.json ./

# Install project dependencies
RUN npm install

# Copy the rest of the application files into the container
COPY . .

# Environment variable: ensure Node built-in modules work with Rollup bundler
ENV ROLLUP_USE_NODE_BUILTINS=true

# Expose the Vite development server port
EXPOSE 5173

# Run Vite in dev mode, binding to all network interfaces for container access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]