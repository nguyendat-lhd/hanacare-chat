"""
SQL Query Fixer
Fix common SQL issues like ambiguous column references, date functions, and type casting
"""
import re

def fix_value_column_casting(sql: str, table_mapping: dict = None) -> str:
    """
    Fix value column casting in aggregate functions
    value columns are VARCHAR but need to be cast to DOUBLE for AVG, SUM, etc.
    
    Args:
        sql: SQL query string
        table_mapping: Dict mapping original table names to escaped names (optional)
    
    Returns:
        Fixed SQL query with value columns cast to DOUBLE
    """
    result_sql = sql
    
    # Import escape_table_name if table_mapping is provided
    escape_func = None
    if table_mapping:
        try:
            from table_utils import escape_table_name
            escape_func = escape_table_name
        except ImportError:
            pass
    
    # Fix aggregate functions with value columns
    # Pattern: AVG(value), AVG(table.value), AVG("table".value), SUM(value), etc.
    # Match table names with or without quotes, with dashes and special chars
    # Pattern matches: table.value or "table".value (where table can have dashes)
    aggregate_pattern = r'(?i)(AVG|SUM|MIN|MAX|AVERAGE)\s*\(\s*((?:"[^"]+"|[^.\s]+)\.)?value\s*\)'
    
    def fix_aggregate_value(match):
        func = match.group(1)
        table_prefix = match.group(2) or ""
        
        # If table prefix exists, keep it as-is (should already be escaped)
        # If not escaped and table_mapping provided, try to escape it
        if table_prefix:
            table_with_dot = table_prefix
            # If not already escaped (no quotes), try to escape it
            if not table_with_dot.startswith('"') and escape_func and table_mapping:
                table_name = table_with_dot.rstrip('.')
                # Find matching table name in mapping
                for orig_name in sorted(table_mapping.keys(), key=len, reverse=True):
                    if table_name == orig_name or orig_name.endswith(table_name) or table_name in orig_name:
                        escaped_table = escape_func(orig_name)
                        return f"{func}(CAST({escaped_table}.value AS DOUBLE))"
            return f"{func}(CAST({table_with_dot}value AS DOUBLE))"
        else:
            return f"{func}(CAST(value AS DOUBLE))"
    
    result_sql = re.sub(aggregate_pattern, fix_aggregate_value, result_sql)
    
    # Also fix arithmetic operations with value columns
    # Pattern: value + 1, table.value + 1, "table".value + 1, etc.
    arithmetic_pattern = r'(?i)((?:"[^"]+"|[^.\s]+)\.)?value\s*([+\-*/])\s*(\d+|value|(?:"[^"]+"|[^.\s]+)\.value)'
    
    def fix_arithmetic_value(match):
        table_prefix = match.group(1) or ""
        operator = match.group(2)
        operand = match.group(3)
        
        # If table prefix exists, keep it as-is (should already be escaped)
        if table_prefix:
            table_with_dot = table_prefix
            # If not already escaped (no quotes), try to escape it
            if not table_with_dot.startswith('"') and escape_func and table_mapping:
                table_name = table_with_dot.rstrip('.')
                # Find matching table name in mapping
                for orig_name in sorted(table_mapping.keys(), key=len, reverse=True):
                    if table_name == orig_name or orig_name.endswith(table_name) or table_name in orig_name:
                        escaped_table = escape_func(orig_name)
                        return f"CAST({escaped_table}.value AS DOUBLE) {operator} {operand}"
            return f"CAST({table_with_dot}value AS DOUBLE) {operator} {operand}"
        else:
            return f"CAST(value AS DOUBLE) {operator} {operand}"
    
    result_sql = re.sub(arithmetic_pattern, fix_arithmetic_value, result_sql)
    
    return result_sql

def fix_date_functions(sql: str) -> str:
    """
    Convert MySQL/PostgreSQL date functions to DuckDB syntax
    Also fix date type casting issues
    
    Args:
        sql: SQL query string
    
    Returns:
        Fixed SQL query with DuckDB date syntax
    """
    result_sql = sql
    
    # Fix DATE_SUB(DATE, INTERVAL N UNIT) -> DATE - INTERVAL 'N UNIT'
    # Pattern: DATE_SUB(date_expr, INTERVAL N DAY/MONTH/YEAR/HOUR/MINUTE/SECOND)
    date_sub_pattern = r'(?i)DATE_SUB\s*\(\s*([^,]+)\s*,\s*INTERVAL\s+(\d+)\s+(DAY|MONTH|YEAR|HOUR|MINUTE|SECOND|WEEK)\s*\)'
    
    def replace_date_sub(match):
        date_expr = match.group(1).strip()
        interval_value = match.group(2)
        interval_unit = match.group(3).lower()
        # DuckDB uses singular form for some units
        if interval_unit == 'days':
            interval_unit = 'day'
        elif interval_unit == 'months':
            interval_unit = 'month'
        elif interval_unit == 'years':
            interval_unit = 'year'
        elif interval_unit == 'hours':
            interval_unit = 'hour'
        elif interval_unit == 'minutes':
            interval_unit = 'minute'
        elif interval_unit == 'seconds':
            interval_unit = 'second'
        elif interval_unit == 'weeks':
            interval_unit = 'week'
        
        return f"{date_expr} - INTERVAL '{interval_value} {interval_unit}'"
    
    result_sql = re.sub(date_sub_pattern, replace_date_sub, result_sql)
    
    # Fix DATE_ADD similarly
    date_add_pattern = r'(?i)DATE_ADD\s*\(\s*([^,]+)\s*,\s*INTERVAL\s+(\d+)\s+(DAY|MONTH|YEAR|HOUR|MINUTE|SECOND|WEEK)\s*\)'
    
    def replace_date_add(match):
        date_expr = match.group(1).strip()
        interval_value = match.group(2)
        interval_unit = match.group(3).lower()
        if interval_unit.endswith('s'):
            interval_unit = interval_unit[:-1]
        return f"{date_expr} + INTERVAL '{interval_value} {interval_unit}'"
    
    result_sql = re.sub(date_add_pattern, replace_date_add, result_sql)
    
    # Fix date column comparisons - cast VARCHAR date columns to TIMESTAMP/DATE
    # Pattern: columnName >= CURRENT_DATE - INTERVAL or columnName <= CURRENT_DATE, etc.
    # Common date column names in health data
    date_column_patterns = [
        r'\b(startDate|endDate|date|timestamp|created_at|updated_at|start_time|end_time)\b',
        r'\b(start_date|end_date|created_date|updated_date)\b',
    ]
    
    # Find comparisons with date columns and CURRENT_DATE/CURRENT_TIMESTAMP
    # Pattern: (table.)column >= CURRENT_DATE - INTERVAL or column <= CURRENT_DATE, etc.
    # Support both >= and ≥ (Unicode)
    
    # First, fix comparisons with CURRENT_DATE/CURRENT_TIMESTAMP and INTERVAL
    # Pattern: (table.)column >= CURRENT_DATE - INTERVAL 'N unit'
    comparison_with_interval_pattern = r'(?i)(\w+\.)?(startDate|endDate|date|timestamp|created_at|updated_at|start_time|end_time|start_date|end_date|created_date|updated_date)\s*([<>=≤≥]+)\s*(CURRENT_DATE|CURRENT_TIMESTAMP|NOW\(\))\s*-\s*INTERVAL\s*[\'"](\d+)\s+(\w+)[\'"]'
    
    def fix_date_comparison_with_interval(match):
        table_prefix = match.group(1) or ""
        column_name = match.group(2)
        operator = match.group(3)
        date_function = match.group(4)
        interval_value = match.group(5)
        interval_unit = match.group(6)
        
        # Normalize interval unit (singular form)
        interval_unit_lower = interval_unit.lower()
        if interval_unit_lower.endswith('s'):
            interval_unit_normalized = interval_unit_lower[:-1]
        else:
            interval_unit_normalized = interval_unit_lower
        
        # Build the fixed comparison with cast
        # Use COALESCE with multiple format attempts for robust date parsing
        # Handles formats like:
        # - "2019-02-12 10:15:05 +0000" (with timezone) - most common in Apple Health
        # - "2019-02-12 10:15:05" (without timezone)
        # - "2019-02-12" (date only)
        if table_prefix:
            # Try strptime with timezone first (most common), then without timezone, then date only, then TRY_CAST
            fixed_column = f"""COALESCE(
                strptime({table_prefix}{column_name}, '%Y-%m-%d %H:%M:%S %z')::TIMESTAMPTZ,
                strptime({table_prefix}{column_name}, '%Y-%m-%d %H:%M:%S')::TIMESTAMPTZ,
                strptime({table_prefix}{column_name}, '%Y-%m-%d')::TIMESTAMPTZ,
                TRY_CAST({table_prefix}{column_name} AS TIMESTAMPTZ)
            )"""
        else:
            fixed_column = f"""COALESCE(
                strptime({column_name}, '%Y-%m-%d %H:%M:%S %z')::TIMESTAMPTZ,
                strptime({column_name}, '%Y-%m-%d %H:%M:%S')::TIMESTAMPTZ,
                strptime({column_name}, '%Y-%m-%d')::TIMESTAMPTZ,
                TRY_CAST({column_name} AS TIMESTAMPTZ)
            )"""
        
        # Normalize operator (≥ -> >=)
        if operator == '≥':
            operator = '>='
        elif operator == '≤':
            operator = '<='
        
        return f"{fixed_column} {operator} {date_function} - INTERVAL '{interval_value} {interval_unit_normalized}'"
    
    result_sql = re.sub(comparison_with_interval_pattern, fix_date_comparison_with_interval, result_sql)
    
    # Second, fix simple comparisons with CURRENT_DATE/CURRENT_TIMESTAMP (no INTERVAL)
    # Pattern: (table.)column >= CURRENT_DATE
    comparison_simple_pattern = r'(?i)(\w+\.)?(startDate|endDate|date|timestamp|created_at|updated_at|start_time|end_time|start_date|end_date|created_date|updated_date)\s*([<>=≤≥]+)\s*(CURRENT_DATE|CURRENT_TIMESTAMP|NOW\(\))(?!\s*[-+])'
    
    def fix_date_comparison_simple(match):
        table_prefix = match.group(1) or ""
        column_name = match.group(2)
        operator = match.group(3)
        date_function = match.group(4)
        
        # Build the fixed comparison with cast
        # Use COALESCE with multiple format attempts for robust date parsing
        if table_prefix:
            fixed_column = f"""COALESCE(
                strptime({table_prefix}{column_name}, '%Y-%m-%d %H:%M:%S %z')::TIMESTAMPTZ,
                strptime({table_prefix}{column_name}, '%Y-%m-%d %H:%M:%S')::TIMESTAMPTZ,
                strptime({table_prefix}{column_name}, '%Y-%m-%d')::TIMESTAMPTZ,
                TRY_CAST({table_prefix}{column_name} AS TIMESTAMPTZ)
            )"""
        else:
            fixed_column = f"""COALESCE(
                strptime({column_name}, '%Y-%m-%d %H:%M:%S %z')::TIMESTAMPTZ,
                strptime({column_name}, '%Y-%m-%d %H:%M:%S')::TIMESTAMPTZ,
                strptime({column_name}, '%Y-%m-%d')::TIMESTAMPTZ,
                TRY_CAST({column_name} AS TIMESTAMPTZ)
            )"""
        
        # Normalize operator (≥ -> >=)
        if operator == '≥':
            operator = '>='
        elif operator == '≤':
            operator = '<='
        
        return f"{fixed_column} {operator} {date_function}"
    
    result_sql = re.sub(comparison_simple_pattern, fix_date_comparison_simple, result_sql)
    
    # Also fix comparisons with date literals
    # Pattern: (table.)column >= '2024-01-01' or column <= '2024-01-01'
    date_literal_pattern = r'(?i)(\w+\.)?(startDate|endDate|date|timestamp|created_at|updated_at|start_time|end_time|start_date|end_date|created_date|updated_date)\s*([<>=≤≥]+)\s*[\'"](\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)[\'"]'
    
    def fix_date_literal_comparison(match):
        table_prefix = match.group(1) or ""
        column_name = match.group(2)
        operator = match.group(3)
        date_literal = match.group(4)
        
        # Use strptime to parse timestamp strings with timezone
        if table_prefix:
            fixed_column = f"strptime({table_prefix}{column_name}, '%Y-%m-%d %H:%M:%S %z')::TIMESTAMPTZ"
        else:
            fixed_column = f"strptime({column_name}, '%Y-%m-%d %H:%M:%S %z')::TIMESTAMPTZ"
        
        # Normalize operator (≥ -> >=)
        if operator == '≥':
            operator = '>='
        elif operator == '≤':
            operator = '<='
        
        return f"{fixed_column} {operator} '{date_literal}'::TIMESTAMPTZ"
    
    result_sql = re.sub(date_literal_pattern, fix_date_literal_comparison, result_sql)
    
    return result_sql

def fix_ambiguous_columns(sql: str, table_names: list) -> str:
    """
    Fix ambiguous column references in SQL query when multiple tables are present.
    Converts comma-separated FROM to UNION ALL queries for each table.
    
    Args:
        sql: SQL query string
        table_names: List of table names that might be in the query
    
    Returns:
        Fixed SQL query with qualified column names or converted to UNION ALL
    """
    if not table_names or len(table_names) < 2:
        return sql
    
    # Check if query has multiple tables (comma-separated in FROM)
    from_match = re.search(r'(?i)FROM\s+(.+?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+HAVING|$|;)', sql, re.DOTALL)
    if not from_match:
        return sql
    
    from_clause = from_match.group(1).strip()
    # Check if multiple tables (comma-separated)
    # Split by comma, but be careful with quoted table names
    tables_in_from = []
    current_table = ""
    in_quotes = False
    for char in from_clause:
        if char == '"':
            in_quotes = not in_quotes
            current_table += char
        elif char == ',' and not in_quotes:
            if current_table.strip():
                tables_in_from.append(current_table.strip().strip('"'))
            current_table = ""
        else:
            current_table += char
    if current_table.strip():
        tables_in_from.append(current_table.strip().strip('"'))
    
    if len(tables_in_from) < 2:
        return sql  # Single table, no ambiguity
    
    # Multiple tables detected - convert to UNION ALL approach
    # Extract SELECT clause
    select_match = re.search(r'(?i)SELECT\s+(.+?)\s+FROM', sql, re.DOTALL)
    if not select_match:
        return sql
    
    select_clause = select_match.group(1).strip()
    
    # Check if there are aggregate functions with unqualified "value"
    # If yes, create separate queries for each table and UNION them
    has_ambiguous_value = re.search(r'(?i)(AVG|SUM|COUNT|MIN|MAX|AVERAGE)\s*\(\s*value\s*\)', select_clause)
    
    if has_ambiguous_value:
        # Multiple tables with ambiguous value columns
        # Strategy: Add table aliases and qualify each AVG(value) with corresponding table
        # Extract all AVG(value) patterns and map them to tables by position
        
        # Count how many AVG(value) or similar patterns
        agg_patterns = re.findall(r'(?i)(AVG|SUM|COUNT|MIN|MAX|AVERAGE)\s*\(\s*value\s*\)', select_clause)
        
        if len(agg_patterns) == len(tables_in_from):
            # Perfect match: each aggregate corresponds to one table
            qualified_parts = []
            for i, (agg_func, table) in enumerate(zip(agg_patterns, tables_in_from)):
                table_escaped = f'"{table}"' if not table.startswith('"') else table
                qualified_parts.append((agg_func, table_escaped))
            
            # Replace in order
            result_clause = select_clause
            for agg_func, table_escaped in qualified_parts:
                pattern = rf'(?i){re.escape(agg_func)}\s*\(\s*value\s*\)'
                replacement = f'{agg_func}({table_escaped}.value)'
                result_clause = re.sub(pattern, replacement, result_clause, count=1)
            
            # Build new SQL with table aliases in FROM
            aliased_tables = []
            for i, table in enumerate(tables_in_from):
                table_escaped = f'"{table}"' if not table.startswith('"') else table
                alias = f"t{i+1}"
                aliased_tables.append(f"{table_escaped} AS {alias}")
            
            # Update FROM clause with aliases
            new_from = ", ".join(aliased_tables)
            result_sql = sql[:select_match.start()] + f'SELECT {result_clause} FROM {new_from}' + sql[from_match.end():]
            return result_sql
        else:
            # Mismatch: use first table for all (fallback)
            first_table = tables_in_from[0]
            table_escaped = f'"{first_table}"' if not first_table.startswith('"') else first_table
            qualified_select = re.sub(
                r'(?i)(AVG|SUM|COUNT|MIN|MAX|AVERAGE)\s*\(\s*value\s*\)',
                lambda m: f'{m.group(1)}({table_escaped}.value)',
                select_clause
            )
            result_sql = sql[:select_match.start()] + f'SELECT {qualified_select} FROM' + sql[select_match.end():]
            return result_sql
    
    # If no ambiguous value, just qualify columns with table aliases
    # Use first table as default (simple heuristic)
    first_table = tables_in_from[0]
    table_escaped = f'"{first_table}"' if not first_table.startswith('"') else first_table
    
    # Qualify unqualified columns
    qualified_select = re.sub(
        r'(?i)\b(value|date|timestamp)\b(?!\s*\.)',
        lambda m: f'{table_escaped}.{m.group(1)}',
        select_clause
    )
    
    # Update SQL
    result_sql = sql[:select_match.start()] + f'SELECT {qualified_select} FROM' + sql[select_match.end():]
    
    return result_sql

