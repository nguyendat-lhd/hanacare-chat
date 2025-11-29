#!/usr/bin/env python3
"""
Test script for MCP Server tools
Usage: python test_tools.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.health_schema import get_health_schema
from tools.health_query import execute_health_query
from tools.user_context import get_user_context

async def test_health_schema(user_id: str = "testuser"):
    """Test health_schema tool"""
    print("=" * 60)
    print("🧪 Testing health_schema tool")
    print("=" * 60)
    print(f"User ID: {user_id}\n")
    
    try:
        result = await get_health_schema(user_id)
        print("✅ Result:")
        import json
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_health_query(user_id: str = "testuser", sql: str = None):
    """Test health_query tool"""
    print("\n" + "=" * 60)
    print("🧪 Testing health_query tool")
    print("=" * 60)
    print(f"User ID: {user_id}")
    
    if not sql:
        # Default query
        sql = "SELECT * FROM steps LIMIT 5"
    
    print(f"SQL: {sql}\n")
    
    try:
        result = await execute_health_query(sql, user_id)
        print("✅ Result:")
        import json
        print(json.dumps(result, indent=2))
        
        if result.get("data"):
            print(f"\n📊 Found {result.get('row_count', 0)} rows")
            if result.get("data"):
                print("\nFirst row:")
                print(json.dumps(result["data"][0], indent=2))
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_user_context(user_id: str = "testuser"):
    """Test get_user_context tool"""
    print("\n" + "=" * 60)
    print("🧪 Testing get_user_context tool")
    print("=" * 60)
    print(f"User ID: {user_id}\n")
    
    try:
        result = await get_user_context(user_id)
        print("✅ Result:")
        import json
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def run_all_tests(user_id: str = "testuser"):
    """Run all tests"""
    print("\n" + "🔧 MCP Server Tools Test Suite" + "\n")
    print(f"Testing with user_id: {user_id}\n")
    
    # Test 1: health_schema
    schema_result = await test_health_schema(user_id)
    
    # Test 2: health_query (if schema works)
    if schema_result and schema_result.get("tables"):
        tables = list(schema_result["tables"].keys())
        if tables:
            # Try query on first table
            first_table = tables[0]
            sql = f"SELECT * FROM {first_table} LIMIT 5"
            await test_health_query(user_id, sql)
            
            # Try aggregate query
            if "steps" in tables:
                sql = "SELECT COUNT(*) as total, AVG(value) as avg_value FROM steps"
                await test_health_query(user_id, sql)
    
    # Test 3: user_context
    await test_user_context(user_id)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP Server tools")
    parser.add_argument("--user-id", default="testuser", help="User ID to test with")
    parser.add_argument("--tool", choices=["schema", "query", "context", "all"], 
                       default="all", help="Which tool to test")
    parser.add_argument("--sql", help="SQL query for health_query test")
    
    args = parser.parse_args()
    
    if args.tool == "schema":
        asyncio.run(test_health_schema(args.user_id))
    elif args.tool == "query":
        asyncio.run(test_health_query(args.user_id, args.sql))
    elif args.tool == "context":
        asyncio.run(test_user_context(args.user_id))
    else:
        asyncio.run(run_all_tests(args.user_id))

