# 🚀 HealthSync AI - Setup Guide

## Quick Start

### 1. Prerequisites Check

Make sure you have:
- ✅ Python 3.11+ installed
- ✅ MongoDB running (local or Atlas)
- ✅ OpenAI API key (get one at https://platform.openai.com/)

### 2. Install Dependencies

```bash
# Setup MCP Server
cd packages/mcp_server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..

# Setup Streamlit App
cd apps/streamlit
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 3. Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env file with your settings:
# MONGODB_URI=mongodb://localhost:27017
# MONGODB_DB=healthsync
# OPENAI_API_KEY=sk-...
```

### 4. Start MongoDB

**Local MongoDB:**
```bash
# macOS (using Homebrew)
brew services start mongodb-community

# Or using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**MongoDB Atlas:**
- Create free account at https://www.mongodb.com/cloud/atlas
- Get connection string and update `MONGODB_URI` in `.env`

### 5. Run the Application

```bash
cd apps/streamlit
source venv/bin/activate
streamlit run app.py
```

Open your browser to `http://localhost:8501`

## 📤 Getting Your Health Data

1. Download **"Simple Health Export CSV"** from App Store
2. Open the app → Select "All" → Export as ZIP
3. Transfer ZIP file to your computer
4. In Streamlit app, go to **Upload** page
5. Upload the ZIP file
6. Start chatting in the **Chat** page!

## 🐛 Troubleshooting

### MCP Server Connection Issues
- Make sure Python path is correct in `utils/mcp_client.py`
- Check that MCP server dependencies are installed

### MongoDB Connection Issues
- Verify MongoDB is running: `mongosh` or check service status
- Check `MONGODB_URI` in `.env` file
- For Atlas: Ensure IP whitelist includes your IP

### OpenAI API Issues
- Verify API key is correct in `.env`
- Check API quota/billing on OpenAI dashboard
- App will work without OpenAI but AI features will be limited

## 📁 Project Structure

```
hanacare-chat/
├── packages/
│   └── mcp_server/          # MCP Server (AI tools)
│       ├── server.py
│       ├── tools/
│       └── requirements.txt
├── apps/
│   └── streamlit/           # Streamlit web app
│       ├── app.py
│       ├── pages/
│       ├── components/
│       ├── utils/
│       └── requirements.txt
├── storage/                 # User data storage
│   └── user_data/
└── .env                     # Environment variables
```

## 🔧 Development

### Running MCP Server Standalone (for testing)
```bash
cd packages/mcp_server
python server.py
```

### Testing MCP Tools
You can test MCP tools with Claude Desktop by configuring it to use this server.

## 📝 Notes

- First time users need to create an account (Sign Up)
- Health data is stored locally in `storage/user_data/{user_id}/`
- Chat history is stored in MongoDB
- All data processing happens locally (privacy-first)

