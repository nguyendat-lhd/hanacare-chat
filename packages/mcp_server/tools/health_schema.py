"""
Tool: Get health data schema
Returns available tables and their columns
"""
import json
import os
from pathlib import Path
import duckdb
from table_utils import escape_table_name

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
            original_name = csv_file.stem  # Keep original name
            # Use original name with temp prefix
            temp_table_name = f"temp_{original_name.replace('-', '_').replace('.', '_')[:50]}"
            escaped_temp_name = escape_table_name(temp_table_name)
            escaped_original_name = escape_table_name(original_name)
            
            try:
                csv_path = str(csv_file).replace("'", "''")  # Escape single quotes
                
                # Try read_csv_auto with error handling options
                try:
                    # Use read_csv_auto without parameters (auto-detects)
                    conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {escaped_temp_name} AS 
                        SELECT * FROM read_csv_auto('{csv_path}')
                    """)
                except Exception as csv_error:
                    # Fallback to pandas if read_csv_auto fails (more forgiving)
                    import pandas as pd
                    try:
                        df = pd.read_csv(
                            csv_file,
                            on_bad_lines='skip',  # Skip bad lines
                            engine='python',
                            quoting=1,
                            escapechar='\\',
                            low_memory=False,
                            encoding='utf-8',
                            errors='replace'
                        )
                        df = df.dropna(how='all')
                        df = df[~df.isnull().all(axis=1)]
                        # Register as temporary table name
                        temp_pandas_name = f"temp_pandas_{normalized_name}"
                        conn.register(temp_pandas_name, df)
                        # Recreate as temp table
                        conn.execute(f"CREATE TABLE IF NOT EXISTS {escaped_temp_name} AS SELECT * FROM {temp_pandas_name}")
                        conn.unregister(temp_pandas_name)
                    except Exception as pandas_error:
                        # If both fail, mark as error but continue
                        schemas[original_name] = {
                            "error": f"CSV parsing failed: {str(csv_error)[:100]}",
                            "file": csv_file.name
                        }
                        continue
                
                # Get column info
                columns_info = conn.execute(
                    f"DESCRIBE {escaped_temp_name}"
                ).fetchall()
                
                schemas[original_name] = {
                    "table_name": original_name,  # Use original name
                    "escaped_name": escaped_original_name,  # Escaped name ready to use in queries
                    "columns": [col[0] for col in columns_info],
                    "column_types": {col[0]: col[1] for col in columns_info},
                    "file": csv_file.name,
                    "row_count": conn.execute(f"SELECT COUNT(*) FROM {escaped_temp_name}").fetchone()[0]
                }
                
                # Clean up temp table
                conn.execute(f"DROP TABLE IF EXISTS {escaped_temp_name}")
            
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

