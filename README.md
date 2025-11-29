# HealthSync AI 🍎

**HealthSync AI** allows you to chat with your own health data. Simply export your data from Apple Health, upload it, and ask questions like "How was my sleep last week?" or "Is my heart rate trending up?".

## 🚀 Features

- **Chat with Data**: Natural language interface to query your health metrics.
- **Privacy First**: Your data is processed securely.
- **Visual Analytics**: AI responses include interactive charts and graphs.
- **No Mobile App Needed**: Web-based interface, works with standard CSV exports.

## 🏗 Architecture

- **Frontend**: React, Vite, TailwindCSS
- **Backend**: Python 3.11, FastAPI
- **Database (App Data)**: MongoDB (User profiles, Chat history)
- **Analytics Engine**: DuckDB (Direct CSV querying for health metrics)
- **AI**: Claude 3.5 Sonnet / GPT-4o via MCP (Model Context Protocol)

## 🛠 Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (Local or Atlas)
- [Simple Health Export CSV](https://apps.apple.com/us/app/simple-health-export-csv/id1535380115) app (for getting your data)

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/hanacare-chat.git
cd hanacare-chat
```

### 2. Backend Setup
```bash
cd packages/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure your env vars
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```

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
