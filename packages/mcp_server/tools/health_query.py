"""
Tool: Execute SQL query on health data
Uses DuckDB to query CSV files directly
"""
import json
import duckdb
from pathlib import Path
from datetime import datetime
from table_utils import escape_table_name
from sql_fixer import fix_ambiguous_columns
import re

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
        
        # Create tables from CSV files - keep original names, just escape them
        table_mapping = {}  # original_name -> escaped_name (for reference)
        failed_files = []
        created_tables = []  # Track successfully created tables
        
        for csv_file in csv_files:
            original_name = csv_file.stem
            # Keep original name, just escape it for SQL
            escaped_name = escape_table_name(original_name)
            table_mapping[original_name] = original_name  # No normalization
            
            # Skip if table already exists (from previous iteration)
            try:
                conn.execute(f"SELECT 1 FROM {escaped_name} LIMIT 1").fetchone()
                created_tables.append(original_name)
                continue  # Table already exists, skip
            except:
                pass  # Table doesn't exist, continue to create it
            
            try:
                # Try with read_csv_auto first (handles most cases)
                csv_path = str(csv_file.resolve()).replace("'", "''").replace("\\", "\\\\")  # Use absolute path
                
                # DuckDB read_csv_auto with options for better error handling
                csv_error = None
                try:
                    # Try with read_csv_auto (simplest, auto-detects everything)
                    # DuckDB read_csv_auto doesn't support named parameters in this way
                    # Use simple call and let it auto-detect
                    conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {escaped_name} AS 
                        SELECT * FROM read_csv_auto('{csv_path}')
                    """)
                    # Verify table was created and has data
                    test_result = conn.execute(f"SELECT COUNT(*) FROM {escaped_name}").fetchone()
                    if test_result and test_result[0] > 0:
                        created_tables.append(original_name)
                    else:
                        # Table created but empty - still add it
                        created_tables.append(original_name)
                except Exception as e:
                    csv_error = e
                    # Check if it's a CSV parsing error (line error, conversion error, etc.)
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ['csv error', 'conversion error', 'line:', 'parser error']):
                        # This is a CSV parsing error, will try pandas fallback
                        pass
                    else:
                        # Other error, try pandas anyway
                        pass
                
                # If DuckDB failed, try pandas fallback
                if csv_error and original_name not in created_tables:
                    # If that fails, try with pandas as fallback (more forgiving)
                    import pandas as pd
                    try:
                        # Read CSV with pandas (handles malformed CSV better)
                        # Use on_bad_lines='skip' to skip problematic lines
                        df = pd.read_csv(
                            csv_file,
                            on_bad_lines='skip',  # Skip bad lines instead of failing
                            engine='python',  # Python engine is more forgiving
                            quoting=1,  # QUOTE_ALL - handle quotes properly
                            escapechar='\\',
                            low_memory=False,
                            encoding='utf-8',
                            errors='replace',  # Replace encoding errors
                            skipinitialspace=True,  # Skip spaces after delimiter
                            skip_blank_lines=True  # Skip blank lines
                        )
                        # Clean the dataframe
                        df = df.dropna(how='all')  # Remove completely empty rows
                        # Remove rows that are completely empty or have all NaN
                        df = df[~df.isnull().all(axis=1)]
                        
                        if df.empty:
                            failed_files.append({
                                "file": csv_file.name,
                                "error": "File is empty after cleaning"
                            })
                            continue
                        
                        # Register as DuckDB table with escaped name (keep original name)
                        # First register with temp name, then create table with escaped name
                        temp_reg_name = f"temp_reg_{original_name.replace('-', '_').replace('.', '_')[:50]}"
                        conn.register(temp_reg_name, df)
                        # Create table with escaped original name from registered dataframe
                        conn.execute(f"CREATE TABLE IF NOT EXISTS {escaped_name} AS SELECT * FROM {temp_reg_name}")
                        conn.unregister(temp_reg_name)
                        # Verify table was created
                        test_result = conn.execute(f"SELECT COUNT(*) FROM {escaped_name}").fetchone()
                        if test_result:
                            created_tables.append(original_name)
                            print(f"✅ Loaded {csv_file.name} via pandas fallback (skipped bad lines)")
                    except Exception as pandas_error:
                        # If both fail, log and continue with next file
                        failed_files.append({
                            "file": csv_file.name,
                            "error": f"CSV error: {str(csv_error)[:100]}, Pandas error: {str(pandas_error)[:100]}"
                        })
                        continue
                elif csv_error:
                    # DuckDB failed but we didn't try pandas - this shouldn't happen
                    failed_files.append({
                        "file": csv_file.name,
                        "error": f"CSV error: {str(csv_error)[:100]}"
                    })
                    continue
            except Exception as e:
                # Catch any other unexpected errors
                failed_files.append({
                    "file": csv_file.name,
                    "error": str(e)[:200]
                })
                continue
        
        # Ensure at least some tables were created
        if not created_tables:
            return {
                "error": f"Failed to load any CSV files. {len(failed_files)} file(s) failed. First error: {failed_files[0].get('error', 'Unknown') if failed_files else 'No files found'}",
                "query": sql,
                "user_id": user_id,
                "failed_files": failed_files[:5]
            }
        
        # Replace table names in SQL query with escaped names (keep original names)
        # Just escape table names that appear in SQL
        normalized_sql = sql
        for original_name in table_mapping.keys():
            escaped_name = escape_table_name(original_name)
            # Replace original name with escaped name in SQL
            # Match after FROM, JOIN, etc.
            pattern = r'(?i)(FROM|JOIN|INTO|UPDATE|TABLE)\s+' + re.escape(original_name) + r'(?=\s|;|$|,|\()'
            normalized_sql = re.sub(pattern, r'\1 ' + escaped_name, normalized_sql)
            # Also replace if quoted (but keep the quotes, just ensure they're there)
            pattern_quoted = r'"' + re.escape(original_name) + r'"'
            if pattern_quoted in normalized_sql:
                normalized_sql = re.sub(pattern_quoted, escaped_name, normalized_sql, flags=re.IGNORECASE)
            # Replace unquoted table names in FROM/JOIN
            pattern_unquoted = r'(?i)(FROM|JOIN)\s+' + re.escape(original_name) + r'(?=\s|,|;|$|WHERE|GROUP|ORDER|HAVING)'
            normalized_sql = re.sub(pattern_unquoted, r'\1 ' + escaped_name, normalized_sql)
        
        # Fix ambiguous column references, date functions, and value column casting
        try:
            from sql_fixer import fix_ambiguous_columns, fix_date_functions, fix_value_column_casting
            # First fix date functions (MySQL/PostgreSQL -> DuckDB)
            normalized_sql = fix_date_functions(normalized_sql)
            # Then fix value column casting (VARCHAR -> DOUBLE for aggregates)
            normalized_sql = fix_value_column_casting(normalized_sql)
            # Finally fix ambiguous columns
            normalized_sql = fix_ambiguous_columns(normalized_sql, list(table_mapping.keys()))
        except Exception as fix_error:
            # If fix fails, continue with original SQL
            print(f"SQL fixer error: {fix_error}")
            pass
        
        # Verify all tables in query exist
        # Extract table names from normalized SQL (simple check)
        for original_table in created_tables:
            escaped_table = escape_table_name(original_table)
            if escaped_table in normalized_sql or original_table in sql:
                # Verify table exists
                try:
                    conn.execute(f"SELECT 1 FROM {escaped_table} LIMIT 1").fetchone()
                except Exception as verify_error:
                    return {
                        "error": f"Table {original_table} exists in mapping but not in database. Error: {str(verify_error)}",
                        "query": sql,
                        "normalized_query": normalized_sql,
                        "created_tables": created_tables,
                        "table_mapping": table_mapping,
                        "user_id": user_id
                    }
        
        # Execute query
        try:
            result = conn.execute(normalized_sql).fetchall()
        except Exception as query_error:
            # If query fails, try to provide helpful error message
            error_msg = str(query_error)
            # Check if it's a table not found error
            if "does not exist" in error_msg or "Table with name" in error_msg:
                # List all available tables
                try:
                    all_tables = conn.execute("SHOW TABLES").fetchall()
                    available_tables = [t[0] for t in all_tables] if all_tables else created_tables
                except:
                    available_tables = created_tables
                
                return {
                    "error": f"Table not found in query. Available tables: {', '.join(available_tables[:10])}",
                    "query": sql,
                    "normalized_query": normalized_sql,
                    "created_tables": created_tables,
                    "table_mapping": table_mapping,
                    "user_id": user_id
                }
            raise
        
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
        
        result = {
            "success": True,
            "data": rows,
            "row_count": len(rows),
            "columns": columns,
            "query": sql,
            "normalized_query": normalized_sql,
            "table_mapping": table_mapping
        }
        
        if failed_files:
            result["warnings"] = f"Failed to load {len(failed_files)} file(s): {[f['file'] for f in failed_files]}"
        
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "query": sql,
            "user_id": user_id
        }
    
    finally:
        conn.close()

