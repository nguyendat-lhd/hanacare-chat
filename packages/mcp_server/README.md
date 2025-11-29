# 🔧 MCP Server - HealthSync AI

MCP Server cung cấp các tools để AI query health data từ CSV files sử dụng DuckDB.

## 📋 Tools Available

1. **`health_schema`** - Lấy schema của health data tables
2. **`health_query`** - Execute SQL query trên health data
3. **`get_user_context`** - Lấy user context từ MongoDB

## 🚀 Cách Chạy MCP Server

### Option 1: Chạy Standalone (Test)

```bash
cd packages/mcp_server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

Server sẽ chạy và chờ input qua stdio.

### Option 2: Test với Claude Desktop

1. Cài đặt Claude Desktop
2. Cấu hình MCP server trong Claude Desktop config
3. Claude Desktop sẽ tự động connect và sử dụng tools

### Option 3: Test Tools Trực Tiếp

Sử dụng script test để gọi tools trực tiếp:

```bash
python test_tools.py
```

## 🧪 Test Tools Trực Tiếp

### Test health_schema

```python
import asyncio
from tools.health_schema import get_health_schema

async def test():
    result = await get_health_schema("testuser")
    print(result)

asyncio.run(test())
```

### Test health_query

```python
import asyncio
from tools.health_query import execute_health_query

async def test():
    sql = "SELECT * FROM steps LIMIT 10"
    result = await execute_health_query(sql, "testuser")
    print(result)

asyncio.run(test())
```

### Test get_user_context

```python
import asyncio
from tools.user_context import get_user_context

async def test():
    result = await get_user_context("testuser")
    print(result)

asyncio.run(test())
```

## 📝 Cấu Trúc Tools

### 1. health_schema

**Input:**
```json
{
  "user_id": "testuser"
}
```

**Output:**
```json
{
  "success": true,
  "user_id": "testuser",
  "tables": {
    "steps": {
      "columns": ["date", "value", "source"],
      "column_types": {"date": "VARCHAR", "value": "INTEGER"},
      "row_count": 30
    }
  }
}
```

### 2. health_query

**Input:**
```json
{
  "sql": "SELECT * FROM steps WHERE date >= '2024-01-01' LIMIT 10",
  "user_id": "testuser"
}
```

**Output:**
```json
{
  "success": true,
  "data": [
    {"date": "2024-01-01", "value": 8500, "source": "iPhone"},
    ...
  ],
  "row_count": 10,
  "columns": ["date", "value", "source"]
}
```

### 3. get_user_context

**Input:**
```json
{
  "user_id": "testuser"
}
```

**Output:**
```json
{
  "success": true,
  "user_id": "testuser",
  "username": "testuser",
  "email": "test@example.com",
  "chat_message_count": 5
}
```

## 🔍 Debugging

### Check CSV Files

```bash
# Xem CSV files của user
ls -la ../../storage/user_data/testuser/

# Xem nội dung một file
head ../../storage/user_data/testuser/steps.csv
```

### Test DuckDB Trực Tiếp

```python
import duckdb
conn = duckdb.connect()

# Test read CSV
result = conn.execute("SELECT * FROM read_csv_auto('../../storage/user_data/testuser/steps.csv') LIMIT 5").fetchall()
print(result)

# Test schema
schema = conn.execute("DESCRIBE SELECT * FROM read_csv_auto('../../storage/user_data/testuser/steps.csv')").fetchall()
print(schema)
```

## ⚠️ Lưu Ý

1. **CSV Files Location**: Tools tìm CSV files trong `storage/user_data/{user_id}/`
2. **DuckDB Connection**: Mỗi tool tạo connection mới (in-memory)
3. **Table Names**: Table name = CSV filename (without .csv extension)
4. **Error Handling**: Tất cả tools return dict với "error" key nếu có lỗi

## 🐛 Troubleshooting

### Lỗi: "No data found for user"
- Kiểm tra CSV files có tồn tại trong `storage/user_data/{user_id}/`
- Đảm bảo user_id đúng

### Lỗi: "No CSV files found"
- Kiểm tra có file `.csv` trong thư mục user
- Kiểm tra permissions

### Lỗi: DuckDB connection failed
- Đảm bảo đã cài `duckdb`: `pip install duckdb`
- Kiểm tra CSV format hợp lệ

### Lỗi: SQL syntax error
- Kiểm tra table names (phải match với CSV filenames)
- Kiểm tra column names trong schema trước

## 📚 Tham Khảo

- [DuckDB Documentation](https://duckdb.org/docs/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

