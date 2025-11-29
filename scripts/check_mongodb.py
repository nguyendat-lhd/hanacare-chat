#!/usr/bin/env python3
"""
Script to check MongoDB connection
Usage: python scripts/check_mongodb.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

if not env_path.exists():
    print("❌ .env file not found!")
    print(f"   Expected at: {env_path}")
    print("   Please run: cp .env.example .env")
    sys.exit(1)

load_dotenv(env_path)

# MongoDB connection
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB", "healthsync")

print("🔍 Checking MongoDB Connection...")
print("-" * 60)
print(f"MongoDB URI: {mongodb_uri}")
print(f"Database Name: {db_name}")
print("-" * 60)

try:
    # Try to connect
    print("\n1️⃣  Attempting to connect...")
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    print("   ✅ Connection successful!")
    
    # Get server info
    print("\n2️⃣  Server Information:")
    server_info = client.server_info()
    print(f"   MongoDB Version: {server_info.get('version', 'Unknown')}")
    print(f"   Server Type: {server_info.get('process', 'Unknown')}")
    
    # List databases (may require auth)
    print("\n3️⃣  Available Databases:")
    try:
        databases = client.list_database_names()
        for db in databases:
            if db not in ['admin', 'config', 'local']:
                print(f"   - {db}")
    except Exception as e:
        print(f"   ⚠️  Cannot list databases (may require auth): {e}")
        print(f"   Continuing with target database check...")
    
    # Check target database
    print(f"\n4️⃣  Checking database '{db_name}':")
    db = client[db_name]
    
    # List collections (may require auth)
    try:
        collections = db.list_collection_names()
        if collections:
            print(f"   ✅ Database exists with {len(collections)} collection(s):")
            for collection in collections:
                try:
                    count = db[collection].count_documents({})
                    print(f"      - {collection}: {count} document(s)")
                except Exception as e:
                    print(f"      - {collection}: (cannot count - may need auth)")
        else:
            print(f"   ✅ Database exists but is empty (no collections yet)")
    except Exception as e:
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            print(f"   ⚠️  Database access requires authentication")
            print(f"   💡 Your MongoDB server has authentication enabled")
            print(f"   💡 Update MONGODB_URI in .env to include credentials:")
            print(f"      mongodb://username:password@localhost:27017/")
        else:
            print(f"   ⚠️  Cannot access database: {e}")
    
    # Test write operation (may require auth)
    auth_required = False
    print("\n5️⃣  Testing write operation...")
    try:
        test_collection = db["_connection_test"]
        test_doc = {"test": "connection", "timestamp": "now"}
        test_collection.insert_one(test_doc)
        test_collection.delete_one(test_doc)
        print("   ✅ Write/Delete test successful!")
    except Exception as e:
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            print("   ⚠️  Write test requires authentication")
            print("   💡 Connection works, but operations need credentials")
            auth_required = True
        else:
            print(f"   ⚠️  Write test failed: {e}")
            auth_required = True
    
    print("\n" + "=" * 60)
    if auth_required:
        print("⚠️  MongoDB connection works but AUTHENTICATION REQUIRED")
        print("=" * 60)
        print("\n💡 To fix:")
        print("   1. Update MONGODB_URI in .env file:")
        print("      mongodb://username:password@localhost:27017/")
        print("   2. Or disable auth (development only):")
        print("      Edit MongoDB config to disable authentication")
        print("\n⚠️  App may not work properly until authentication is configured")
    else:
        print("✅ MongoDB connection check PASSED!")
        print("=" * 60)
    
    client.close()
    
except ConnectionFailure as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Check if MongoDB is running:")
    print("      - Local: brew services list | grep mongodb")
    print("      - Docker: docker ps | grep mongodb")
    print("   2. Verify MONGODB_URI in .env file")
    print("   3. For Atlas: Check network access and credentials")
    sys.exit(1)
    
except ServerSelectionTimeoutError as e:
    print(f"\n❌ Server selection timeout: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. MongoDB server might not be running")
    print("   2. Check firewall/network settings")
    print("   3. Verify MONGODB_URI is correct")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"   Error type: {type(e).__name__}")
    sys.exit(1)

