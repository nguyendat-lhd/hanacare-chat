"""
Tool: Get user context from MongoDB
Returns user profile and preferences
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

async def get_user_context(user_id: str) -> dict:
    """
    Get user context from MongoDB
    
    Args:
        user_id: User ID to get context for
    
    Returns:
        Dictionary with user context
    """
    try:
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB", "healthsync")
        
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        
        # Get user profile
        user = db.users.find_one({"user_id": user_id})
        
        if not user:
            return {
                "error": "User not found",
                "user_id": user_id
            }
        
        # Get recent chat history count
        chat_count = db.chat_messages.count_documents({"user_id": user_id})
        
        # Get file metadata
        files = list(db.file_metadata.find({"user_id": user_id}).sort("upload_date", -1).limit(5))
        
        return {
            "success": True,
            "user_id": user_id,
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "chat_message_count": chat_count,
            "recent_files": [
                {
                    "filename": f.get("filename", ""),
                    "upload_date": str(f.get("upload_date", "")),
                    "csv_count": f.get("csv_count", 0)
                }
                for f in files
            ]
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_id
        }

