"""
CSV Validator
Validate and pre-load CSV files into DuckDB to ensure they're queryable
"""
import duckdb
from pathlib import Path
import sys

# Add MCP tools to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "packages" / "mcp_server" / "tools"))
from table_utils import escape_table_name

def validate_csv_files(storage_path: Path, max_files: int = 10) -> dict:
    """
    Validate CSV files can be loaded into DuckDB
    
    Args:
        storage_path: Path to directory containing CSV files
        max_files: Maximum number of files to validate (for performance)
    
    Returns:
        Dictionary with validation results
    """
    csv_files = list(storage_path.glob("*.csv"))
    
    if not csv_files:
        return {
            "success": False,
            "error": "No CSV files found",
            "validated": 0,
            "failed": []
        }
    
    conn = duckdb.connect()
    validated = []
    failed = []
    
    try:
        # Validate first few files (for performance)
        files_to_validate = csv_files[:max_files]
        
        for csv_file in files_to_validate:
            try:
                original_name = csv_file.stem
                # Keep original name, just escape it
                escaped_name = escape_table_name(original_name)
                
                # Try to read CSV
                csv_path = str(csv_file).replace("'", "''").replace("\\", "\\\\")
                
                try:
                    # Try with read_csv_auto (auto-detects schema)
                    conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {escaped_name} AS 
                        SELECT * FROM read_csv_auto('{csv_path}')
                    """)
                    # Verify it worked
                    count = conn.execute(f"SELECT COUNT(*) FROM {escaped_name}").fetchone()[0]
                    validated.append({
                        "file": csv_file.name,
                        "table_name": original_name,
                        "row_count": count,
                        "status": "success"
                    })
                    # Clean up temp table
                    conn.execute(f"DROP TABLE IF EXISTS {escaped_name}")
                except Exception as csv_error:
                    # Try with pandas fallback (more forgiving with bad lines)
                    import pandas as pd
                    try:
                        df = pd.read_csv(
                            csv_file,
                            on_bad_lines='skip',  # Skip bad lines
                            engine='python',  # More forgiving
                            quoting=1,
                            escapechar='\\',
                            low_memory=False,
                            encoding='utf-8',
                            errors='replace',  # Replace encoding errors
                            skipinitialspace=True,  # Skip spaces after delimiter
                            skip_blank_lines=True  # Skip blank lines
                        )
                        df = df.dropna(how='all')
                        df = df[~df.isnull().all(axis=1)]
                        
                        if not df.empty:
                            validated.append({
                                "file": csv_file.name,
                                "table_name": original_name,
                                "row_count": len(df),
                                "status": "success (pandas)",
                                "warning": "Some rows may have been skipped due to parsing errors"
                            })
                        else:
                            failed.append({
                                "file": csv_file.name,
                                "error": "File is empty after cleaning"
                            })
                    except Exception as pandas_error:
                        failed.append({
                            "file": csv_file.name,
                            "error": f"CSV error: {str(csv_error)[:100]}, Pandas error: {str(pandas_error)[:100]}"
                        })
            except Exception as e:
                failed.append({
                    "file": csv_file.name,
                    "error": str(e)[:200]
                })
        
        return {
            "success": len(validated) > 0,
            "validated": len(validated),
            "failed": len(failed),
            "total_files": len(csv_files),
            "validated_files": validated,
            "failed_files": failed
        }
    
    finally:
        conn.close()

