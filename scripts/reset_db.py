#!/usr/bin/env python3
"""
Utility script to reset the entire database
WARNING: This will delete ALL users and data!
Usage: python scripts/reset_db.py
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import shutil

# Load environment variables
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# MongoDB connection
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB", "healthsync")

def reset_database():
    """Reset entire database - delete all collections"""
    try:
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        
        # List collections
        collections = db.list_collection_names()
        
        if not collections:
            print("✅ Database is already empty")
            return True
        
        print(f"⚠️  WARNING: This will delete ALL data from database '{db_name}'")
        print(f"   Collections to delete: {', '.join(collections)}")
        
        confirm = input("\nType 'RESET' to confirm: ")
        if confirm != "RESET":
            print("❌ Cancelled")
            return False
        
        # Delete all collections
        for collection_name in collections:
            db[collection_name].drop()
            print(f"   ✅ Deleted collection: {collection_name}")
        
        # Delete all storage directories
        storage_path = project_root / "storage" / "user_data"
        if storage_path.exists():
            for user_dir in storage_path.iterdir():
                if user_dir.is_dir():
                    shutil.rmtree(user_dir)
                    print(f"   ✅ Deleted storage: {user_dir.name}")
        
        print("\n✅ Database reset successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

if __name__ == "__main__":
    reset_database()

