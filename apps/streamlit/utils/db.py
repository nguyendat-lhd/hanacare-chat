"""
Database Utilities
MongoDB connection and operations
"""
import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB", "healthsync")

def get_db():
    """Get MongoDB database instance"""
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        return client[db_name]
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        raise

def save_chat_message(user_id: str, role: str, content: str, chart_data: dict = None):
    """Save chat message to MongoDB"""
    try:
        db = get_db()
        message = {
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "chart_data": chart_data
        }
        db.chat_messages.insert_one(message)
    except Exception as e:
        print(f"Error saving chat message: {e}")

def get_chat_history(user_id: str, limit: int = 50):
    """Get chat history for user"""
    try:
        db = get_db()
        messages = list(
            db.chat_messages
            .find({"user_id": user_id})
            .sort("timestamp", 1)
            .limit(limit)
        )
        # Convert ObjectId to string and remove chart_data for display
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            if "chart_data" in msg and msg["chart_data"]:
                # Keep chart_data but it might be large
                pass
        return messages
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []

def save_file_metadata(user_id: str, metadata: dict):
    """Save file upload metadata"""
    try:
        db = get_db()
        metadata["user_id"] = user_id
        metadata["upload_date"] = datetime.now()
        db.file_metadata.insert_one(metadata)
    except Exception as e:
        print(f"Error saving file metadata: {e}")

def get_file_metadata(user_id: str):
    """Get file metadata for user"""
    try:
        db = get_db()
        files = list(
            db.file_metadata
            .find({"user_id": user_id})
            .sort("upload_date", -1)
        )
        for f in files:
            f["_id"] = str(f["_id"])
        return files
    except Exception as e:
        print(f"Error getting file metadata: {e}")
        return []

