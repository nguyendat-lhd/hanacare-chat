# 🚀 Hướng Dẫn Chạy HealthSync AI

Hướng dẫn chi tiết từng bước để chạy ứng dụng HealthSync AI.

## 📋 Yêu Cầu Hệ Thống

- **Python 3.11+** (kiểm tra: `python3 --version`)
- **MongoDB** (Local hoặc Atlas)
- **OpenAI API Key** (để dùng tính năng AI chat)
- **Git** (để clone project)

## 🔧 Bước 1: Kiểm Tra Python

```bash
python3 --version
# Phải >= 3.11
```

Nếu chưa có Python 3.11+, cài đặt:
- **macOS**: `brew install python@3.11`
- **Linux**: `sudo apt install python3.11`
- **Windows**: Download từ [python.org](https://www.python.org/)

## 🗄️ Bước 2: Setup MongoDB

### Option A: MongoDB Local (Khuyến nghị cho development)

**macOS (Homebrew):**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Docker (Dễ nhất):**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Kiểm tra MongoDB đã chạy:**
```bash
mongosh
# Hoặc
docker ps | grep mongodb
```

### Option B: MongoDB Atlas (Cloud - Free tier)

1. Đăng ký tại [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Tạo cluster miễn phí
3. Lấy connection string (dạng: `mongodb+srv://user:pass@cluster.mongodb.net/`)
4. Lưu connection string để dùng ở bước sau

## 🔑 Bước 3: Lấy OpenAI API Key

1. Đăng ký/đăng nhập tại [platform.openai.com](https://platform.openai.com/)
2. Vào **API Keys** → **Create new secret key**
3. Copy API key (dạng: `sk-...`)
4. Lưu để dùng ở bước sau

> **Lưu ý**: Nếu không có OpenAI API key, app vẫn chạy được nhưng tính năng AI chat sẽ bị hạn chế.

## 📦 Bước 4: Clone và Setup Project

```bash
# 1. Di chuyển vào thư mục dự án (nếu chưa có)
cd /Users/macbook/dev/hanacare-chat

# 2. Tạo file .env từ template
cp .env.example .env

# 3. Mở file .env và chỉnh sửa
# macOS/Linux:
nano .env
# Hoặc dùng editor khác: code .env, vim .env, etc.

# 4. Điền thông tin vào .env:
# MONGODB_URI=mongodb://localhost:27017  (hoặc Atlas connection string)
# MONGODB_DB=healthsync
# OPENAI_API_KEY=sk-your-api-key-here
```

**Ví dụ file .env:**
```env
# MongoDB Local
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=healthsync

# Hoặc MongoDB Atlas
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
# MONGODB_DB=healthsync

# OpenAI API Key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
```

## 🐍 Bước 5: Setup MCP Server

```bash
# 1. Vào thư mục MCP Server
cd packages/mcp_server

# 2. Tạo virtual environment
python3 -m venv venv

# 3. Kích hoạt virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 4. Cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Quay lại thư mục gốc
cd ../..
```

## 🌐 Bước 6: Setup Streamlit App

```bash
# 1. Vào thư mục Streamlit
cd apps/streamlit

# 2. Tạo virtual environment
python3 -m venv venv

# 3. Kích hoạt virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 4. Cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Quay lại thư mục gốc
cd ../..
```

## 🚀 Bước 7: Chạy Ứng Dụng

### Cách 1: Dùng Script (Khuyến nghị)

```bash
# Từ thư mục gốc của project
chmod +x run.sh
./run.sh
```

### Cách 2: Chạy Thủ Công

```bash
# 1. Đảm bảo MongoDB đang chạy
# Kiểm tra:
mongosh
# Hoặc
docker ps | grep mongodb

# 2. Vào thư mục Streamlit
cd apps/streamlit

# 3. Kích hoạt virtual environment
source venv/bin/activate  # macOS/Linux
# hoặc venv\Scripts\activate  # Windows

# 4. Chạy Streamlit
streamlit run app.py
```

### Kết Quả

Ứng dụng sẽ mở tự động trong browser tại:
```
http://localhost:8501
```

Nếu không tự mở, copy URL trên terminal và paste vào browser.

## 📱 Bước 8: Sử Dụng Ứng Dụng

### 1. Tạo Tài Khoản

- Mở app trong browser
- Click tab **"Sign Up"**
- Nhập:
  - **User ID**: Tên đăng nhập (ví dụ: `testuser`)
  - **Email**: (tùy chọn)
  - **Password**: Mật khẩu (tối thiểu 4 ký tự)
- Click **"Sign Up"**

### 2. Upload Health Data

1. **Trên iPhone:**
   - Tải app **"Simple Health Export CSV"** từ App Store
   - Mở app → Chọn **"All"** → Export as **ZIP**
   - Chuyển file ZIP sang máy tính (AirDrop, email, Files app)

2. **Trong Streamlit App:**
   - Đăng nhập với tài khoản vừa tạo
   - Vào page **"📤 Upload"**
   - Click **"Browse files"** → Chọn file ZIP
   - Đợi upload và extract hoàn tất
   - Sẽ thấy danh sách CSV files đã upload

### 3. Chat với Health Data

1. Vào page **"💬 Chat"**
2. Nhập câu hỏi, ví dụ:
   - "How many steps did I take last week?"
   - "What was my average heart rate yesterday?"
   - "Show me my sleep data for the past 7 days"
3. AI sẽ:
   - Generate SQL query
   - Query data từ CSV files
   - Trả lời bằng natural language
   - Hiển thị chart nếu có data

### 4. Xem Dashboard

- Vào page **"📊 Dashboard"**
- Xem health summary cards
- Xem detailed charts
- Explore data tables

## 🐛 Troubleshooting

### Lỗi: "MongoDB connection failed"

**Giải pháp:**
```bash
# Kiểm tra MongoDB đang chạy
mongosh
# Hoặc
docker ps | grep mongodb

# Nếu chưa chạy, start MongoDB:
# macOS:
brew services start mongodb-community

# Docker:
docker start mongodb
```

### Lỗi: "MCP Server connection failed"

**Giải pháp:**
1. Kiểm tra MCP server dependencies đã cài:
```bash
cd packages/mcp_server
source venv/bin/activate
pip list | grep mcp
```

2. Nếu thiếu, cài lại:
```bash
pip install -r requirements.txt
```

### Lỗi: "Module not found"

**Giải pháp:**
```bash
# Đảm bảo đang ở đúng virtual environment
which python  # Phải trỏ đến venv/bin/python

# Cài lại dependencies
pip install -r requirements.txt
```

### Lỗi: "OpenAI API key invalid"

**Giải pháp:**
1. Kiểm tra API key trong `.env` file
2. Đảm bảo có `sk-` ở đầu
3. Kiểm tra API key còn valid trên OpenAI dashboard
4. Restart Streamlit app sau khi sửa `.env`

### Lỗi: "No data found for user"

**Giải pháp:**
1. Đảm bảo đã upload ZIP file thành công
2. Kiểm tra file CSV trong `storage/user_data/{user_id}/`
3. Thử upload lại file ZIP

### Port 8501 đã được sử dụng

**Giải pháp:**
```bash
# Tìm process đang dùng port 8501
lsof -ti:8501

# Kill process đó
kill -9 $(lsof -ti:8501)

# Hoặc chạy Streamlit trên port khác
streamlit run app.py --server.port 8502
```

## 📝 Checklist Trước Khi Chạy

- [ ] Python 3.11+ đã cài
- [ ] MongoDB đang chạy (local hoặc Atlas)
- [ ] File `.env` đã tạo và điền đầy đủ
- [ ] MCP Server dependencies đã cài (`packages/mcp_server/venv`)
- [ ] Streamlit dependencies đã cài (`apps/streamlit/venv`)
- [ ] Virtual environment đã activate
- [ ] Đã tạo tài khoản trong app
- [ ] Đã upload health data (ZIP file)

## 🎯 Quick Commands Reference

```bash
# Start MongoDB (macOS)
brew services start mongodb-community

# Start MongoDB (Docker)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Check MongoDB
mongosh

# Run Streamlit
cd apps/streamlit
source venv/bin/activate
streamlit run app.py

# Hoặc dùng script
./run.sh
```

## 💡 Tips

1. **Development Mode**: Streamlit tự động reload khi code thay đổi
2. **Multiple Users**: Mỗi user có thư mục riêng trong `storage/user_data/`
3. **Chat History**: Lưu trong MongoDB, có thể xem lại
4. **Performance**: Với data lớn, có thể mất vài giây để query
5. **Privacy**: Tất cả data xử lý local, không gửi lên server (trừ OpenAI API)

## 📞 Cần Giúp Đỡ?

- Xem `SETUP.md` để biết thêm chi tiết
- Xem `IMPLEMENTATION.md` để hiểu kiến trúc
- Check logs trong terminal để debug

---

**Chúc bạn sử dụng vui vẻ! 🎉**

