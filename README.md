# HealthSync AI 🍎

**HealthSync AI** allows you to chat with your own health data. Simply export your data from Apple Health, upload it, and ask questions like "How was my sleep last week?" or "Is my heart rate trending up?".

## 🚀 Features

- **Chat with Data**: Natural language interface to query your health metrics.
- **Privacy First**: Your data is processed securely.
- **Visual Analytics**: AI responses include interactive charts and graphs.
- **No Mobile App Needed**: Web-based interface, works with standard CSV exports.

## 🏗 Architecture

- **Frontend**: Streamlit (Python-based web app)
- **MCP Server**: Python 3.11+ (Model Context Protocol server for AI tools)
- **Database (App Data)**: MongoDB (User profiles, Chat history)
- **Analytics Engine**: DuckDB (Direct CSV querying for health metrics)
- **AI**: GPT-4o / Claude 3.5 Sonnet via OpenAI API + MCP tools

## 🛠 Prerequisites

- Python 3.11+
- MongoDB (Local or Atlas)
- OpenAI API Key (for AI chat features)
- [Simple Health Export CSV](https://apps.apple.com/us/app/simple-health-export-csv/id1535380115) app (for getting your data)

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB (Local or Atlas)
- OpenAI API Key

### Installation Steps

1. **Setup Environment**
```bash
cp .env.example .env
# Edit .env with your MongoDB URI and OpenAI API key
```

2. **Install Dependencies**
```bash
# MCP Server
cd packages/mcp_server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Streamlit App
cd ../../apps/streamlit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

3. **Start MongoDB** (if using local)
```bash
# macOS
brew services start mongodb-community

# Or Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

4. **Run Application**
```bash
cd apps/streamlit
source venv/bin/activate
streamlit run app.py
```

App will open at `http://localhost:8501`

> 📖 **Xem hướng dẫn chi tiết**: [HUONG_DAN_CHAY.md](./HUONG_DAN_CHAY.md) (Tiếng Việt)

## 📊 Data Ingestion Flow

1. Open **Simple Health Export CSV** on your iPhone.
2. Select "All" and export as ZIP.
3. Upload the ZIP file to the HealthSync Web Dashboard.
4. The system unzips and indexes the CSVs using DuckDB.
5. Start chatting!

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

[MIT](https://choosealicense.com/licenses/mit/)
