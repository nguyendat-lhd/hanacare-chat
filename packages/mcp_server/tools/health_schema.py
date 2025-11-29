"""
Tool: Get health data schema
Returns available tables and their columns
"""
import json
import os
from pathlib import Path
import duckdb

async def get_health_schema(user_id: str) -> dict:
    """
    Get schema of available health data tables
    
    Args:
        user_id: User ID to get schema for
    
    Returns:
        Dictionary with table schemas
    """
    # Get project root (3 levels up from tools/)
    project_root = Path(__file__).parent.parent.parent.parent
    storage_path = project_root / "storage" / "user_data" / user_id
    
    if not storage_path.exists():
        return {
            "error": "No data found for user",
            "user_id": user_id,
            "tables": {}
        }
    
    # Find all CSV files
    csv_files = list(storage_path.glob("*.csv"))
    
    if not csv_files:
        return {
            "error": "No CSV files found",
            "user_id": user_id,
            "tables": {}
        }
    
    # Connect to DuckDB
    conn = duckdb.connect()
    schemas = {}
    
    try:
        for csv_file in csv_files:
            table_name = csv_file.stem  # e.g., "steps", "heart_rate"
            
            try:
                # Read CSV to get schema
                conn.execute(f"CREATE TABLE IF NOT EXISTS temp_{table_name} AS SELECT * FROM read_csv_auto('{csv_file}')")
                
                # Get column info
                columns_info = conn.execute(
                    f"DESCRIBE temp_{table_name}"
                ).fetchall()
                
                schemas[table_name] = {
                    "columns": [col[0] for col in columns_info],
                    "column_types": {col[0]: col[1] for col in columns_info},
                    "file": csv_file.name,
                    "row_count": conn.execute(f"SELECT COUNT(*) FROM temp_{table_name}").fetchone()[0]
                }
                
                # Clean up temp table
                conn.execute(f"DROP TABLE IF EXISTS temp_{table_name}")
            
            except Exception as e:
                schemas[table_name] = {
                    "error": str(e),
                    "file": csv_file.name
                }
        
        return {
            "success": True,
            "user_id": user_id,
            "tables": schemas,
            "table_count": len(schemas)
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_id,
            "tables": {}
        }
    
    finally:
        conn.close()

