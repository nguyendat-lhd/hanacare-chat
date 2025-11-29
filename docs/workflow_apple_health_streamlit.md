# 🍎 Workflow Hoàn Hảo: iPhone Health App → Streamlit Dashboard

## Tổng Quan Workflow

```
iPhone Health App
      ↓ Export XML
Health Export XML (export.xml)
      ↓
Apple Health MCP Server (Parser + Converter)
      ↓ JSON Format
Streamlit UI → Chart / Dashboard / Chatbot
```

---

## 1. Giai Đoạn 1: Export Dữ Liệu Từ iPhone

### 1.1. Cách Export XML Từ Health App

**Option A: Sử dụng App "Health Export" (Recommended)**
- Tải app **"Health Export"** từ App Store (hoặc app tương tự).
- Mở app → Chọn **"Export All Data"** → Chọn format **XML**.
- File sẽ được lưu vào Files app hoặc AirDrop sang máy tính.

**Option B: Export Trực Tiếp Từ iPhone Settings**
- Settings → Privacy & Security → Health → Data Export
- Chọn **"Export All Health Data"** → File XML sẽ được tạo.

**Output:**
- File `export.xml` (có thể rất lớn, từ vài MB đến vài GB tùy lượng dữ liệu).

---

## 2. Giai Đoạn 2: Apple Health MCP Server - Parser & Converter

### 2.1. Kiến Trúc MCP Server

**Nhiệm vụ của MCP Server:**
1. **Parse XML** từ HealthKit export.
2. **Convert sang JSON** (structured format dễ query).
3. **Normalize data** (chuẩn hóa units, timestamps).
4. **Index data** để query nhanh (có thể dùng DuckDB hoặc in-memory index).

### 2.2. Cấu Trúc MCP Server

**File Structure:**
```
apple-health-mcp/
├── server.py              # MCP Server main
├── parser/
│   ├── xml_parser.py       # Parse XML từ HealthKit
│   ├── data_normalizer.py # Normalize units, timestamps
│   └── json_converter.py  # Convert sang JSON
├── tools/
│   ├── health_schema.py   # Tool: get_schema() → list tables/columns
│   ├── health_query.py    # Tool: query(sql) → execute SQL trên data
│   └── health_metrics.py  # Tool: get_metrics() → quick stats
└── storage/
    └── user_data/         # Lưu parsed JSON files
```

### 2.3. MCP Tools Cần Implement

**Tool 1: `parse_health_xml(xml_path: str) → dict`**
- Input: Đường dẫn file `export.xml`.
- Process:
  - Parse XML bằng `xml.etree.ElementTree` hoặc `lxml`.
  - Extract các record types: `HKQuantityTypeIdentifier`, `HKCategoryTypeIdentifier`, `HKWorkoutTypeIdentifier`.
  - Normalize timestamps (convert sang UTC, ISO format).
  - Normalize units (steps → count, heartRate → bpm, distance → meters).
- Output: JSON structure:
  ```json
  {
    "metadata": {
      "export_date": "2024-01-15T10:00:00Z",
      "device_info": {...}
    },
    "records": {
      "steps": [...],
      "heartRate": [...],
      "sleep": [...],
      "workouts": [...]
    }
  }
  ```

**Tool 2: `get_health_schema() → dict`**
- Trả về schema của các bảng/metrics có sẵn.
- Output:
  ```json
  {
    "tables": {
      "steps": ["timestamp", "value", "source"],
      "heartRate": ["timestamp", "value", "unit", "source"],
      "sleep": ["startDate", "endDate", "value", "category"]
    }
  }
  ```

**Tool 3: `query_health_data(sql: str) → list`**
- Input: SQL query (AI tự viết).
- Process:
  - Load parsed JSON vào DuckDB (in-memory hoặc file-based).
  - Execute SQL query.
- Output: JSON array of results.

**Tool 4: `get_health_summary(days: int = 7) → dict`**
- Quick summary: steps, avg heart rate, sleep hours, workouts.
- Output: JSON với key metrics.

---

## 3. Giai Đoạn 3: Streamlit UI - Dashboard & Chatbot

### 3.1. Kiến Trúc Streamlit App

**File Structure:**
```
streamlit-app/
├── app.py                 # Main Streamlit app
├── pages/
│   ├── dashboard.py       # Health metrics dashboard
│   ├── chat.py            # AI Chatbot interface
│   └── upload.py          # Upload XML file
├── components/
│   ├── charts.py          # Chart components (Plotly/Altair)
│   ├── health_cards.py    # Summary cards
│   └── chat_ui.py         # Chat interface
├── utils/
│   ├── mcp_client.py      # Connect to MCP Server
│   └── data_processor.py  # Process JSON từ MCP
└── requirements.txt
```

### 3.2. Luồng Hoạt Động Trong Streamlit

**Step 1: Upload & Parse (Page: Upload)**
```python
# app.py hoặc pages/upload.py
uploaded_file = st.file_uploader("Upload Health Export XML", type="xml")
if uploaded_file:
    # Gọi MCP Server tool: parse_health_xml()
    result = mcp_client.call_tool("parse_health_xml", {"xml_path": temp_path})
    st.success("✅ Data parsed successfully!")
    # Lưu parsed JSON vào session state
    st.session_state.health_data = result
```

**Step 2: Dashboard (Page: Dashboard)**
```python
# pages/dashboard.py
if "health_data" in st.session_state:
    data = st.session_state.health_data
    
    # Render charts
    st.subheader("📊 Health Metrics Overview")
    
    # Steps chart
    steps_df = pd.DataFrame(data["records"]["steps"])
    st.line_chart(steps_df.set_index("timestamp")["value"])
    
    # Heart rate chart
    hr_df = pd.DataFrame(data["records"]["heartRate"])
    st.area_chart(hr_df.set_index("timestamp")["value"])
    
    # Sleep summary
    sleep_df = pd.DataFrame(data["records"]["sleep"])
    st.bar_chart(sleep_df.groupby("date")["duration"].sum())
```

**Step 3: AI Chatbot (Page: Chat)**
```python
# pages/chat.py
if "health_data" in st.session_state:
    user_query = st.chat_input("Ask about your health data...")
    
    if user_query:
        # Gọi MCP Server tool: query_health_data()
        # AI tự viết SQL dựa trên query
        sql = ai_generate_sql(user_query)  # AI model generate SQL
        results = mcp_client.call_tool("query_health_data", {"sql": sql})
        
        # AI trả lời + render chart nếu có data
        response = ai_generate_response(user_query, results)
        st.chat_message("assistant").write(response)
        
        # Render chart nếu AI trả về data
        if results:
            df = pd.DataFrame(results)
            st.plotly_chart(create_chart(df))
```

### 3.3. Components Cần Build

**1. Chart Components (`components/charts.py`)**
- Sử dụng **Plotly** hoặc **Altair** (tích hợp tốt với Streamlit).
- Functions:
  - `plot_steps_timeline(data)` → Line chart steps theo ngày.
  - `plot_heart_rate_distribution(data)` → Histogram heart rate.
  - `plot_sleep_quality(data)` → Bar chart sleep hours.
  - `plot_workout_summary(data)` → Pie chart workout types.

**2. Health Cards (`components/health_cards.py`)**
- Summary cards hiển thị:
  - Total steps (hôm nay, tuần này).
  - Avg heart rate.
  - Sleep hours (đêm qua).
  - Active calories.

**3. Chat UI (`components/chat_ui.py`)**
- Streamlit chat interface với:
  - Message history.
  - Auto-scroll.
  - Chart rendering trong message (nếu AI trả về data).

---

## 4. Integration: MCP Server ↔ Streamlit

### 4.1. Communication Pattern

**Option A: MCP Server chạy như Background Process**
- Streamlit app start → spawn MCP Server process.
- Streamlit gọi MCP tools qua **stdio** hoặc **HTTP** (nếu MCP hỗ trợ HTTP transport).

**Option B: MCP Server chạy độc lập (Recommended)**
- MCP Server chạy như service riêng (có thể trên cùng server hoặc remote).
- Streamlit app connect qua **MCP Client SDK** (Python).

**Implementation:**
```python
# utils/mcp_client.py
from mcp import ClientSession, StdioServerParameters
import subprocess

class MCPHealthClient:
    def __init__(self):
        self.session = None
    
    async def connect(self):
        server_params = StdioServerParameters(
            command="python",
            args=["path/to/mcp_server.py"]
        )
        self.session = ClientSession(server_params)
        await self.session.initialize()
    
    async def call_tool(self, tool_name: str, args: dict):
        result = await self.session.call_tool(tool_name, args)
        return result
```

### 4.2. Data Flow

```
User uploads XML
    ↓
Streamlit saves to temp file
    ↓
Streamlit calls MCP tool: parse_health_xml()
    ↓
MCP Server parses XML → JSON
    ↓
MCP Server saves JSON to storage/user_id/
    ↓
MCP returns JSON to Streamlit
    ↓
Streamlit stores in session_state
    ↓
User queries in Chat
    ↓
Streamlit calls MCP tool: query_health_data(sql)
    ↓
MCP Server loads JSON → DuckDB → Execute SQL
    ↓
MCP returns results
    ↓
Streamlit renders chart + AI response
```

---

## 5. Tech Stack Chi Tiết

### 5.1. MCP Server Stack
- **Python 3.11+**
- **MCP SDK** (`mcp` package)
- **DuckDB** (query engine)
- **lxml** hoặc `xml.etree` (XML parsing)
- **pandas** (data manipulation)

### 5.2. Streamlit Stack
- **Streamlit** (main framework)
- **Plotly** hoặc **Altair** (charts)
- **pandas** (data processing)
- **MCP Client SDK** (connect to MCP Server)
- **OpenAI/Anthropic SDK** (AI model cho chatbot)

---

## 6. Lộ Trình Triển Khai (Implementation Timeline)

### Phase 1: MCP Server - XML Parser (2-3 giờ)
- [ ] Setup MCP Server structure.
- [ ] Implement XML parser (parse HealthKit XML).
- [ ] Implement JSON converter.
- [ ] Test với sample XML file.

### Phase 2: MCP Server - Tools (2-3 giờ)
- [ ] Implement `parse_health_xml` tool.
- [ ] Implement `get_health_schema` tool.
- [ ] Implement `query_health_data` tool (integrate DuckDB).
- [ ] Test tools với Claude Desktop.

### Phase 3: Streamlit - Upload & Parse (1-2 giờ)
- [ ] Build upload page.
- [ ] Integrate MCP client.
- [ ] Test upload → parse flow.

### Phase 4: Streamlit - Dashboard (2-3 giờ)
- [ ] Build chart components.
- [ ] Build health cards.
- [ ] Integrate với parsed data.

### Phase 5: Streamlit - AI Chatbot (3-4 giờ)
- [ ] Build chat UI.
- [ ] Integrate AI model (Claude/GPT).
- [ ] Implement SQL generation từ natural language.
- [ ] Implement chart rendering trong chat.

### Phase 6: Polish & Testing (1-2 giờ)
- [ ] Error handling.
- [ ] UI/UX improvements.
- [ ] End-to-end testing.

---

## 7. Ưu Điểm Của Workflow Này

✅ **Trực tiếp từ iPhone**: Không cần app trung gian (như "Simple Health Export CSV").  
✅ **Chuẩn Apple HealthKit**: XML format là chuẩn chính thức từ Apple.  
✅ **MCP Protocol**: Tận dụng MCP để AI có thể query data một cách linh hoạt.  
✅ **Streamlit nhanh**: Prototype dashboard và chatbot rất nhanh.  
✅ **Scalable**: Có thể mở rộng thêm metrics, charts, AI features.

---

## 8. Rủi Ro & Giải Pháp

**Rủi ro 1: XML file quá lớn (>1GB)**
- **Giải pháp**: Parse streaming (không load toàn bộ vào memory), chỉ parse metrics cần thiết.

**Rủi ro 2: MCP Server chậm khi query data lớn**
- **Giải pháp**: Index data bằng DuckDB, cache kết quả query thường dùng.

**Rủi ro 3: Streamlit session timeout**
- **Giải pháp**: Lưu parsed JSON vào file/database, không chỉ dựa vào session_state.

---

## 9. Tài Liệu Tham Khảo

- [Apple HealthKit Export Format](https://developer.apple.com/documentation/healthkit)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [neiltron/apple-health-mcp](https://github.com/neiltron/apple-health-mcp) - Reference implementation
- [Streamlit Documentation](https://docs.streamlit.io/)

---

**Next Steps:**
1. Review workflow này với team.
2. Quyết định: MCP Server chạy local hay remote?
3. Bắt đầu implement Phase 1 (MCP Server XML Parser).

