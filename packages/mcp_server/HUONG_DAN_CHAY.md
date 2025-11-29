# 🚀 Hướng Dẫn Chạy MCP Server Tools

Hướng dẫn chi tiết cách test và chạy các tools trong MCP Server.

## 📋 Yêu Cầu

- Python 3.11+
- Đã cài dependencies: `pip install -r requirements.txt`
- Có sample data hoặc real data trong `storage/user_data/{user_id}/`

## 🎯 Cách 1: Test Tools Trực Tiếp (Khuyến nghị)

### Bước 1: Setup

```bash
cd packages/mcp_server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Bước 2: Chạy Test Script

```bash
# Test tất cả tools
python test_tools.py

# Test với user_id khác
python test_tools.py --user-id admin

# Test một tool cụ thể
python test_tools.py --tool schema
python test_tools.py --tool query
python test_tools.py --tool context

# Test với SQL query tùy chỉnh
python test_tools.py --tool query --sql "SELECT COUNT(*) FROM steps"
```

### Kết Quả Mẫu

```
🔧 MCP Server Tools Test Suite

Testing with user_id: testuser

============================================================
🧪 Testing health_schema tool
============================================================
User ID: testuser

✅ Result:
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

## 🎯 Cách 2: Test Từng Tool Riêng Lẻ

### Test health_schema

Tạo file `test_schema.py`:

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tools.health_schema import get_health_schema

async def main():
    result = await get_health_schema("testuser")
    import json
    print(json.dumps(result, indent=2))

asyncio.run(main())
```

Chạy:
```bash
python test_schema.py
```

### Test health_query

Tạo file `test_query.py`:

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tools.health_query import execute_health_query

async def main():
    sql = "SELECT * FROM steps LIMIT 10"
    result = await execute_health_query(sql, "testuser")
    import json
    print(json.dumps(result, indent=2))

asyncio.run(main())
```

Chạy:
```bash
python test_query.py
```

### Test get_user_context

Tạo file `test_context.py`:

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tools.user_context import get_user_context

async def main():
    result = await get_user_context("testuser")
    import json
    print(json.dumps(result, indent=2))

asyncio.run(main())
```

Chạy:
```bash
python test_context.py
```

## 🎯 Cách 3: Test DuckDB Trực Tiếp

Tạo file `test_duckdb.py`:

```python
import duckdb
from pathlib import Path

# Get CSV file path
project_root = Path(__file__).parent.parent.parent
csv_file = project_root / "storage" / "user_data" / "testuser" / "steps.csv"

# Connect to DuckDB
conn = duckdb.connect()

# Read CSV directly
print("📊 Reading CSV file...")
result = conn.execute(f"SELECT * FROM read_csv_auto('{csv_file}') LIMIT 5").fetchall()
print("First 5 rows:")
for row in result:
    print(row)

# Get schema
print("\n📋 Schema:")
schema = conn.execute(f"DESCRIBE SELECT * FROM read_csv_auto('{csv_file}')").fetchall()
for col in schema:
    print(f"  {col[0]}: {col[1]}")

# Aggregate query
print("\n📈 Aggregate:")
agg = conn.execute(f"""
    SELECT 
        COUNT(*) as total,
        AVG(value) as avg_value,
        MIN(value) as min_value,
        MAX(value) as max_value
    FROM read_csv_auto('{csv_file}')
""").fetchone()
print(f"  Total rows: {agg[0]}")
print(f"  Average: {agg[1]:.2f}")
print(f"  Min: {agg[2]}")
print(f"  Max: {agg[3]}")

conn.close()
```

Chạy:
```bash
python test_duckdb.py
```

## 🎯 Cách 4: Chạy MCP Server Standalone

### Chạy Server

```bash
cd packages/mcp_server
python server.py
```

Server sẽ chạy và chờ input qua stdio (theo MCP protocol).

### Test với MCP Client

Tạo file `test_mcp_client.py`:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path

async def main():
    server_path = Path(__file__).parent / "server.py"
    
    server_params = StdioServerParameters(
        command="python",
        args=[str(server_path)]
    )
    
    read_stream, write_stream = await stdio_client(server_params)
    session = ClientSession(read_stream, write_stream)
    await session.initialize()
    
    # List tools
    tools = await session.list_tools()
    print("Available tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Call health_schema
    result = await session.call_tool("health_schema", {"user_id": "testuser"})
    print("\nhealth_schema result:")
    print(result.content[0].text if result.content else "No content")
    
    await session.close()

asyncio.run(main())
```

## 📝 Ví Dụ SQL Queries

### Query Steps Data

```sql
-- Get all steps
SELECT * FROM steps LIMIT 10

-- Get steps for last 7 days
SELECT * FROM steps 
WHERE date >= date('now', '-7 days')
ORDER BY date DESC

-- Aggregate steps
SELECT 
    date,
    SUM(value) as total_steps,
    AVG(value) as avg_steps
FROM steps
GROUP BY date
ORDER BY date DESC
```

### Query Heart Rate

```sql
-- Get heart rate readings
SELECT * FROM heart_rate LIMIT 10

-- Average heart rate per day
SELECT 
    DATE(timestamp) as date,
    AVG(value) as avg_heart_rate,
    MIN(value) as min_hr,
    MAX(value) as max_hr
FROM heart_rate
GROUP BY DATE(timestamp)
ORDER BY date DESC
```

### Query Sleep

```sql
-- Get sleep data
SELECT * FROM sleep LIMIT 10

-- Average sleep duration
SELECT 
    AVG(duration_hours) as avg_sleep_hours,
    MIN(duration_hours) as min_sleep,
    MAX(duration_hours) as max_sleep
FROM sleep
```

### Cross-table Queries

```sql
-- Steps and sleep correlation
SELECT 
    s.date,
    s.value as steps,
    sl.duration_hours as sleep_hours
FROM steps s
LEFT JOIN sleep sl ON s.date = sl.date
ORDER BY s.date DESC
LIMIT 10
```

## 🐛 Troubleshooting

### Lỗi: "No data found for user"

**Nguyên nhân**: Không tìm thấy CSV files

**Giải pháp**:
```bash
# Kiểm tra thư mục
ls -la ../../storage/user_data/testuser/

# Tạo sample data nếu chưa có
cd ../../apps/streamlit
python -c "from utils.sample_data import generate_sample_data; from pathlib import Path; generate_sample_data('testuser', Path('../../storage/user_data/testuser'))"
```

### Lỗi: "Table not found"

**Nguyên nhân**: Table name không đúng

**Giải pháp**:
```bash
# Xem available tables
python test_tools.py --tool schema

# Sử dụng đúng table name trong SQL
```

### Lỗi: "Column not found"

**Nguyên nhân**: Column name không đúng

**Giải pháp**:
```bash
# Xem schema để biết column names
python test_tools.py --tool schema

# Kiểm tra CSV file
head ../../storage/user_data/testuser/steps.csv
```

## 📚 Tài Liệu Tham Khảo

- [DuckDB SQL Reference](https://duckdb.org/docs/sql/introduction)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

