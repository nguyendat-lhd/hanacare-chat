"""
Tool: Execute SQL query on health data
Uses DuckDB to query CSV files directly
"""
import json
import duckdb
from pathlib import Path
from datetime import datetime

async def execute_health_query(sql: str, user_id: str) -> dict:
    """
    Execute SQL query on user's health data using DuckDB
    
    Args:
        sql: SQL query string
        user_id: User ID whose data to query
    
    Returns:
        Dictionary with query results
    """
    # Get project root (3 levels up from tools/)
    project_root = Path(__file__).parent.parent.parent.parent
    storage_path = project_root / "storage" / "user_data" / user_id
    
    if not storage_path.exists():
        return {
            "error": "No data found for user",
            "user_id": user_id
        }
    
    # Connect to DuckDB
    conn = duckdb.connect()
    
    try:
        # Register CSV files as tables
        csv_files = list(storage_path.glob("*.csv"))
        
        if not csv_files:
            return {
                "error": "No CSV files found",
                "user_id": user_id
            }
        
        # Create tables from CSV files
        for csv_file in csv_files:
            table_name = csv_file.stem  # e.g., "steps", "heart_rate"
            # Use read_csv_auto to automatically detect schema
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} AS 
                SELECT * FROM read_csv_auto('{csv_file}')
            """)
        
        # Execute query
        result = conn.execute(sql).fetchall()
        
        # Get column names
        columns = [desc[0] for desc in conn.description] if conn.description else []
        
        # Convert to list of dicts
        rows = []
        for row in result:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert datetime objects to strings
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[col] = value
            rows.append(row_dict)
        
        return {
            "success": True,
            "data": rows,
            "row_count": len(rows),
            "columns": columns,
            "query": sql
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "query": sql,
            "user_id": user_id
        }
    
    finally:
        conn.close()

