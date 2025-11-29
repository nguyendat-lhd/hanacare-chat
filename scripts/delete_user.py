#!/usr/bin/env python3
"""
Utility script to delete a user from MongoDB
Usage: python scripts/delete_user.py <user_id>
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# MongoDB connection
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB", "healthsync")

def delete_user(user_id: str):
    """Delete user and all associated data"""
    try:
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        
        # Check if user exists
        user = db.users.find_one({"user_id": user_id})
        if not user:
            print(f"❌ User '{user_id}' not found in database")
            return False
        
        # Delete user data
        print(f"🗑️  Deleting user '{user_id}' and all associated data...")
        
        # Delete user
        result_users = db.users.delete_one({"user_id": user_id})
        
        # Delete chat messages
        result_messages = db.chat_messages.delete_many({"user_id": user_id})
        
        # Delete file metadata
        result_files = db.file_metadata.delete_many({"user_id": user_id})
        
        # Delete storage files
        storage_path = project_root / "storage" / "user_data" / user_id
        if storage_path.exists():
            import shutil
            shutil.rmtree(storage_path)
            print(f"   ✅ Deleted storage directory: {storage_path}")
        
        print(f"\n✅ User '{user_id}' deleted successfully!")
        print(f"   - User record: {result_users.deleted_count}")
        print(f"   - Chat messages: {result_messages.deleted_count}")
        print(f"   - File metadata: {result_files.deleted_count}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return False

def list_users():
    """List all users in database"""
    try:
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        
        users = list(db.users.find({}, {"user_id": 1, "email": 1, "created_at": 1}))
        
        if not users:
            print("No users found in database")
            return
        
        print("\n📋 Users in database:")
        print("-" * 60)
        for user in users:
            print(f"  User ID: {user.get('user_id', 'N/A')}")
            print(f"  Email: {user.get('email', 'N/A')}")
            print(f"  Created: {user.get('created_at', 'N/A')}")
            print("-" * 60)
    
    except Exception as e:
        print(f"❌ Error listing users: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/delete_user.py <user_id>")
        print("   or: python scripts/delete_user.py --list")
        print("\nExamples:")
        print("  python scripts/delete_user.py testuser")
        print("  python scripts/delete_user.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_users()
    else:
        user_id = sys.argv[1]
        confirm = input(f"⚠️  Are you sure you want to delete user '{user_id}'? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            delete_user(user_id)
        else:
            print("❌ Cancelled")

