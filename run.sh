#!/bin/bash
# Quick start script for HealthSync AI

echo "🍎 Starting HealthSync AI..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your MongoDB URI and OpenAI API key"
    exit 1
fi

# Check if MongoDB is running (basic check)
if ! pgrep -x "mongod" > /dev/null && ! pgrep -f "mongo" > /dev/null; then
    echo "⚠️  MongoDB doesn't seem to be running."
    echo "   Please start MongoDB before running the app."
    echo "   Local: brew services start mongodb-community"
    echo "   Docker: docker run -d -p 27017:27017 --name mongodb mongo:latest"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Activate Streamlit venv and run
cd apps/streamlit

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Starting Streamlit..."
streamlit run app.py

