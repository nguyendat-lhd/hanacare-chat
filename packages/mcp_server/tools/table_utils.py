"""
Table name utilities
Normalize and escape table names for SQL
"""
import re

def normalize_table_name(filename: str) -> str:
    """
    Normalize table name from filename
    Replace special characters with underscores and ensure valid SQL identifier
    
    Args:
        filename: CSV filename (with or without extension)
    
    Returns:
        Normalized table name safe for SQL
    """
    # Remove extension if present
    name = filename.replace('.csv', '')
    
    # Replace special characters with underscore
    # Keep only alphanumeric and underscore
    normalized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Remove consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    # Ensure it starts with letter or underscore (SQL requirement)
    if normalized and normalized[0].isdigit():
        normalized = '_' + normalized
    
    # If empty after normalization, use default
    if not normalized:
        normalized = 'table_' + str(abs(hash(name)) % 10000)
    
    return normalized

def escape_table_name(table_name: str) -> str:
    """
    Escape table name for SQL (use double quotes)
    
    Args:
        table_name: Table name to escape
    
    Returns:
        Escaped table name
    """
    # Use double quotes to escape identifiers in DuckDB
    return f'"{table_name}"'

def replace_table_names_in_sql(sql: str, table_mapping: dict) -> str:
    """
    Replace table names in SQL query with normalized/escaped names
    
    Args:
        sql: Original SQL query
        table_mapping: Dict mapping original table names to normalized names
    
    Returns:
        SQL query with replaced table names
    """
    if not table_mapping:
        return sql
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_mappings = sorted(table_mapping.items(), key=lambda x: len(x[0]), reverse=True)
    
    result_sql = sql
    
    for original_name, normalized_name in sorted_mappings:
        # Escape normalized name
        escaped_name = escape_table_name(normalized_name)
        
        # Create patterns for different cases
        # Note: We need to handle table names with dashes, which don't work with \b word boundary
        
        # Pattern 1: Original name after SQL keywords (FROM, JOIN, etc.)
        # Match: FROM table_name, JOIN table_name, etc.
        pattern1 = r'(?i)(FROM|JOIN|INTO|UPDATE|TABLE)\s+' + re.escape(original_name) + r'(?=\s|;|$|,|\()'
        result_sql = re.sub(pattern1, r'\1 ' + escaped_name, result_sql)
        
        # Pattern 2: Original name with double quotes
        pattern2 = r'"' + re.escape(original_name) + r'"'
        result_sql = re.sub(pattern2, escaped_name, result_sql, flags=re.IGNORECASE)
        
        # Pattern 3: Original name as standalone (not after keyword, not quoted)
        # Match table name that's not part of a string and not already escaped
        # Use lookbehind/lookahead to ensure it's not part of another word
        pattern3 = r'(?<![a-zA-Z0-9_])' + re.escape(original_name) + r'(?![a-zA-Z0-9_-])'
        # Only replace if the original name still exists and escaped name is not present
        if original_name in result_sql:
            result_sql = re.sub(pattern3, escaped_name, result_sql, flags=re.IGNORECASE)
        
        # Pattern 4: Normalized name after SQL keywords (if AI already normalized it)
        pattern4 = r'(?i)(FROM|JOIN|INTO|UPDATE|TABLE)\s+' + re.escape(normalized_name) + r'(?=\s|;|$|,|\()'
        result_sql = re.sub(pattern4, r'\1 ' + escaped_name, result_sql)
        
        # Pattern 5: Normalized name with quotes
        pattern5 = r'"' + re.escape(normalized_name) + r'"'
        result_sql = re.sub(pattern5, escaped_name, result_sql, flags=re.IGNORECASE)
        
        # Pattern 6: Normalized name as standalone (not quoted, not after keyword)
        pattern6 = r'(?<![a-zA-Z0-9_])' + re.escape(normalized_name) + r'(?![a-zA-Z0-9_])'
        if normalized_name in result_sql and escaped_name not in result_sql:
            result_sql = re.sub(pattern6, escaped_name, result_sql, flags=re.IGNORECASE)
    
    return result_sql

