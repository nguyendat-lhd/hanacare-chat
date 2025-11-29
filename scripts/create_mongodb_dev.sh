#!/bin/bash
# Script to create MongoDB without authentication for development

echo "🔧 Creating MongoDB without authentication for development..."
echo ""
echo "This will create a new MongoDB container without auth."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Stop existing MongoDB if running
docker stop mongodb 2>/dev/null || true
docker rm mongodb 2>/dev/null || true

# Create new MongoDB without auth
docker run -d \
  --name mongodb-dev \
  -p 27017:27017 \
  mongo:latest

echo ""
echo "✅ MongoDB created successfully!"
echo "   Container name: mongodb-dev"
echo "   Port: 27017"
echo "   Authentication: Disabled"
echo ""
echo "💡 Update your .env file:"
echo "   MONGODB_URI=mongodb://localhost:27017"
echo ""
echo "Now you can run: python scripts/seed_users.py"

