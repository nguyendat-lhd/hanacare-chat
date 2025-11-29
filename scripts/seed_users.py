#!/usr/bin/env python3
"""
Script to seed sample users into MongoDB
Usage: python scripts/seed_users.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import hashlib

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

if not env_path.exists():
    print("❌ .env file not found!")
    print(f"   Expected at: {env_path}")
    sys.exit(1)

load_dotenv(env_path)

# MongoDB connection
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB", "healthsync")

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_users():
    """Seed sample users"""
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db = client[db_name]
        users_collection = db.users
        
        # Sample users
        sample_users = [
            {
                "user_id": "admin",
                "password_hash": hash_password("admin123"),
                "email": "admin@healthsync.ai",
                "created_at": datetime.now()
            },
            {
                "user_id": "testuser",
                "password_hash": hash_password("test123"),
                "email": "test@example.com",
                "created_at": datetime.now()
            },
            {
                "user_id": "demo",
                "password_hash": hash_password("demo123"),
                "email": "demo@healthsync.ai",
                "created_at": datetime.now()
            },
            {
                "user_id": "user1",
                "password_hash": hash_password("password123"),
                "email": "user1@example.com",
                "created_at": datetime.now()
            }
        ]
        
        print("🌱 Seeding sample users...")
        print("-" * 60)
        
        created_count = 0
        skipped_count = 0
        
        for user in sample_users:
            user_id = user["user_id"]
            
            # Check if user already exists
            existing = users_collection.find_one({"user_id": user_id})
            if existing:
                print(f"⏭️  User '{user_id}' already exists, skipping...")
                skipped_count += 1
            else:
                users_collection.insert_one(user)
                print(f"✅ Created user: {user_id} (password: {user_id}123)")
                created_count += 1
        
        print("-" * 60)
        print(f"\n📊 Summary:")
        print(f"   ✅ Created: {created_count} user(s)")
        print(f"   ⏭️  Skipped: {skipped_count} user(s)")
        
        print(f"\n📋 Sample Users Created:")
        print("-" * 60)
        for user in sample_users:
            if not users_collection.find_one({"user_id": user["user_id"]}):
                continue
            password = user["user_id"] + "123"
            print(f"   User ID: {user['user_id']}")
            print(f"   Password: {password}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print("-" * 60)
        
        print("\n💡 You can now login with any of these users!")
        print("   Example: User ID: 'testuser', Password: 'test123'")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        print(f"\n💡 Troubleshooting:")
        print("   1. Make sure MongoDB is running")
        print("   2. Check MONGODB_URI in .env file")
        print("   3. If MongoDB requires auth, update MONGODB_URI with credentials")
        return False

if __name__ == "__main__":
    seed_users()

