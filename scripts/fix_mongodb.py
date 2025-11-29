#!/usr/bin/env python3
"""
Script to fix MongoDB connection issues
This script will help diagnose and fix MongoDB connection problems
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

if not env_path.exists():
    print("❌ .env file not found!")
    sys.exit(1)

load_dotenv(env_path)

mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB", "healthsync")

print("🔧 MongoDB Connection Fixer")
print("=" * 60)
print(f"MongoDB URI: {mongodb_uri}")
print(f"Database Name: {db_name}")
print("=" * 60)

# Test 1: Basic connection
print("\n1️⃣  Testing basic connection...")
try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("   ✅ Basic connection successful!")
except ConnectionFailure as e:
    print(f"   ❌ Connection failed: {e}")
    print("\n💡 MongoDB server might not be running")
    print("   Start MongoDB:")
    print("   - Docker: docker run -d -p 27017:27017 --name mongodb mongo:latest")
    print("   - Homebrew: brew services start mongodb-community")
    sys.exit(1)
except ServerSelectionTimeoutError as e:
    print(f"   ❌ Server timeout: {e}")
    print("\n💡 MongoDB server is not reachable")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Database access
print("\n2️⃣  Testing database access...")
try:
    db = client[db_name]
    # Try to list collections
    collections = db.list_collection_names()
    print(f"   ✅ Database access successful!")
    print(f"   Found {len(collections)} collection(s)")
except OperationFailure as e:
    error_msg = str(e)
    print(f"   ❌ Operation failed: {error_msg}")
    
    if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
        print("\n🔐 Authentication Required")
        print("-" * 60)
        print("Your MongoDB requires authentication.")
        print("\nOption A: Create MongoDB without auth (Development)")
        print("   Run: ./scripts/create_mongodb_dev.sh")
        print("\nOption B: Add credentials to .env")
        print("   Update MONGODB_URI to:")
        print("   mongodb://username:password@localhost:27017/")
        print("\nOption C: Create user in MongoDB")
        print("   1. Connect to MongoDB:")
        print("      mongosh")
        print("   2. Create user:")
        print("      use admin")
        print("      db.createUser({")
        print("        user: 'healthsync',")
        print("        pwd: 'password123',")
        print("        roles: [{ role: 'readWrite', db: '" + db_name + "' }]")
        print("      })")
        print("   3. Update .env:")
        print("      MONGODB_URI=mongodb://healthsync:password123@localhost:27017/")
    else:
        print(f"\n❌ Unknown operation error: {error_msg}")
    sys.exit(1)
except Exception as e:
    print(f"   ⚠️  Warning: {e}")

# Test 3: Write operation
print("\n3️⃣  Testing write operation...")
try:
    test_collection = db["_connection_test"]
    test_doc = {"test": "connection", "timestamp": "now"}
    test_collection.insert_one(test_doc)
    test_collection.delete_one(test_doc)
    print("   ✅ Write operation successful!")
except OperationFailure as e:
    print(f"   ❌ Write failed: {e}")
    if "authentication" in str(e).lower():
        print("   💡 Authentication required for write operations")
except Exception as e:
    print(f"   ⚠️  Write test warning: {e}")

print("\n" + "=" * 60)
print("✅ MongoDB connection is working!")
print("=" * 60)
print("\n💡 You can now:")
print("   1. Run: python scripts/seed_users.py")
print("   2. Start the Streamlit app")

client.close()

