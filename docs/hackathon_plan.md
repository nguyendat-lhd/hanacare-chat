# 🍎 HealthSync AI - Hackathon Master Plan

## 1. Mục tiêu (Goal)

Xây dựng một ứng dụng cho phép người dùng **trò chuyện với dữ liệu sức khỏe** của chính mình một cách dễ dàng nhất.

- **Không** cần export file thủ công.
- **Không** cần biết kỹ thuật.
- Truy cập Web Dashboard -> Upload/Import Data (hoặc dùng dữ liệu mẫu) -> Chat.

## 2. Luồng người dùng (User Flow)

1.  **Web Dashboard:** Người dùng mở web trên máy tính.
2.  **Data Ingestion:** Người dùng upload file zip từ app "Simple Health Export CSV".
3.  **Chat:** Người dùng hỏi: _"Hôm qua tôi ngủ có ngon không?"_ -> AI trả lời kèm biểu đồ phân tích.

## 3. Kiến trúc hệ thống (Architecture)



### A. Backend & MCP Server (The Brain)

- **Nhiệm vụ:**
  1.  Nhận dữ liệu từ App và lưu vào Database.
  2.  Quản lý authentication và user data.
  3.  Chạy MCP Server để cung cấp "công cụ" (tools) cho AI tra cứu dữ liệu.
- **Công nghệ:** Python 3.11 (FastAPI), **DuckDB** (analytics), **MongoDB** (auth + app data), MCP SDK.
- **Architecture Reference:** Follow theo kiến trúc của [neiltron/apple-health-mcp](https://github.com/neiltron/apple-health-mcp).
  - Sử dụng **DuckDB** để query trực tiếp file CSV (không cần import vào DB cứng).
  - Input format: Output của app **Simple Health Export CSV**.

#### 🗄️ Dual Database Strategy

Chúng ta sử dụng **2 databases** cho 2 mục đích khác nhau:

**1. MongoDB - Application Data:**

- **User authentication** (Simple JWT)
- **User profiles**
- **Chat history** (sessions, messages)
- **File metadata** (tracking uploaded CSVs)

**Tại sao cần MongoDB?**

- ✅ Flexible Schema (JSON-like), phù hợp lưu chat history.
- ✅ Dễ dàng tích hợp với Python.
- ✅ Free tier (MongoDB Atlas) hoặc chạy Docker local.

**2. DuckDB - Health Metrics Analytics:**

- **Time-series health data** (steps, heart rate, sleep)
- **Architecture:** Query trực tiếp trên file CSV (Parquet/CSV querying) giống `apple-health-mcp`.
- **MCP tool queries** (AI viết SQL để query CSV)

#### 🛠 Database Selection: Tại sao chọn DuckDB cho Health Metrics?

Chúng ta chọn **DuckDB** cho health analytics vì đặc thù của dữ liệu sức khỏe là **Time-series Analytics** (Phân tích chuỗi thời gian). DuckDB tối ưu cho việc query và tính toán trên các file CSV/Parquet mà không cần import vào database truyền thống, rất phù hợp với kiến trúc xử lý file export từ HealthKit.

### B. Web Frontend (The Interface)

- **Nhiệm vụ:** Giao diện Chat và hiển thị Biểu đồ.
- **Công nghệ:** React + Tailwind CSS.
- **Điểm nhấn:** Khi AI trả lời, nó không chỉ hiện text mà hiện cả Widget biểu đồ (VD: Biểu đồ cột so sánh giấc ngủ các ngày).

## 4. Lộ trình triển khai (Hackathon Timeline)

Chúng ta sẽ chia làm 5 giai đoạn (Sprints):

### Giai đoạn 0: Setup Infrastructure (30 phút)

- **Database Setup:**
  - MongoDB: Setup connection string (Atlas or Local).
  - DuckDB: Install `duckdb` python package.
- **API Server (Python 3.11 + FastAPI):**
  - Setup FastAPI project structure.
  - Implement JWT Auth (Login/Signup).
  - Endpoint: `POST /api/v1/ingest` (nhận dữ liệu upload file zip).

### Giai đoạn 2: Data Ingestion (Web-based) (2-3 giờ)

- **Data Upload:**
  - Xây dựng chức năng upload file Zip (Simple Health Export CSV).
  - Unzip và lưu vào folder `storage/user_id/`.
  - Setup DuckDB  - Parse dữ liệu và lưu vào folder storage.
- **Verification:**
  - Check MongoDB có user/metadata chưa.
  - Test query thử 1 file CSV bằng DuckDB.

### Giai đoạn 3: AI Brain - MCP Server (3-4 giờ)

- **MCP Tools Development (Follow `apple-health-mcp`):**
  - Tool: `health_schema()` → Trả về cấu trúc bảng (columns của CSV).
  - Tool: `health_query(sql)` → Thực thi SQL query trên DuckDB (AI tự viết SQL).
  - Tool: `get_user_context(user_id)` → Query MongoDB (preferences)al).
- **MCP Server:**
  - Setup stdio transport
  - Test với Claude Desktop
  - Verify tools hoạt động: "Show my steps for last 7 days"

### Giai đoạn 4: Web Dashboard (4-5 giờ)

  - Integrate với `POST /api/chat` endpoint
  - **Save chat to MongoDB:**
    - Auto-create session on first message
    - Insert messages to `chat_messages` collection
  - Polling hoặc WebSocket (nếu kịp) để update chat.
- **Generative UI:**
  - Nếu AI trả về JSON data → Render biểu đồ (Recharts)
  - Health cards (daily summary, trends)

### Giai đoạn 5: Polish & Demo (1-2 giờ)

- **Seed Data:** Script generate 30 ngày dữ liệu giả cho demo
- **Styling:** Medical/Clean theme (Teal/White/Grey)
- **Error Handling:** Graceful fallbacks
- **Demo Video:** Record quy trình: Login → Upload Data/Select Sample → Web Chat → AI Analysis

## 5. Các rủi ro & Giải pháp (Risk Assessment)

- **Rủi ro:** MongoDB Atlas free tier giới hạn connection.
  - **Giải pháp:** Dùng local MongoDB cho demo hoặc quản lý connection pool tốt.

- **Rủi ro:** Dữ liệu quá lớn, xử lý lâu.
  - **Giải pháp:** Chỉ xử lý dữ liệu 30 ngày gần nhất cho bản Hackathon.
- **Rủi ro:** MCP Server không connect được với Claude.
  - **Giải pháp:** Test sớm với Claude Desktop, có backup plan dùng function calling trực tiếp.

---

## 6. Tech Stack Summary

**Frontend:**

- React + Vite + TailwindCSS
- Supabase Auth helpers
- Recharts (data visualization)

**Backend:**

**Backend:**

- Python 3.11
- FastAPI (API server)
- DuckDB (health metrics analytics)
- MongoDB (auth, user data, chat history)
- MCP SDK (AI tool integration)



**AI:**

- Claude 3.5 Sonnet hoặc GPT-4o
- MCP Protocol cho tool calling

---

**Câu hỏi cho bạn:**


1. Bạn muốn dùng model AI nào? (Claude 3.5 Sonnet hay GPT-4o đều tốt cho việc gọi tool).
2. Bạn sẽ chạy MongoDB local hay dùng Atlas?
