"""
Session Management
Persist authentication state across page reloads
"""
import streamlit as st
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from utils.db import get_db

# Session file path (in user's temp directory)
def get_session_file_path(user_id: str = None) -> Path:
    """Get session file path"""
    project_root = Path(__file__).parent.parent.parent.parent
    session_dir = project_root / "storage" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    if user_id:
        # Create session file name from user_id hash
        session_hash = hashlib.md5(user_id.encode()).hexdigest()
        return session_dir / f"{session_hash}.json"
    return session_dir

def create_session(user_id: str) -> str:
    """Create a session token for user"""
    import secrets
    session_token = secrets.token_urlsafe(32)
    
    session_data = {
        "user_id": user_id,
        "token": session_token,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()  # 7 days expiry
    }
    
    # Save to file
    session_file = get_session_file_path(user_id)
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    # Also save to MongoDB for cross-device access
    try:
        db = get_db()
        db.sessions.update_one(
            {"user_id": user_id},
            {"$set": session_data},
            upsert=True
        )
    except:
        pass  # If MongoDB fails, file-based session still works
    
    return session_token

def validate_session(session_token: str = None, user_id: str = None) -> dict:
    """Validate session token"""
    if not session_token and not user_id:
        return None
    
    # Try to get from file first
    if user_id:
        session_file = get_session_file_path(user_id)
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    # Check expiry
                    expires_at = datetime.fromisoformat(session_data.get("expires_at", "2000-01-01"))
                    if datetime.now() < expires_at:
                        if not session_token or session_data.get("token") == session_token:
                            return session_data
            except:
                pass
    
    # Try MongoDB
    try:
        db = get_db()
        query = {}
        if user_id:
            query["user_id"] = user_id
        if session_token:
            query["token"] = session_token
        
        session_data = db.sessions.find_one(query)
        if session_data:
            # Check expiry
            expires_at = datetime.fromisoformat(session_data.get("expires_at", "2000-01-01"))
            if datetime.now() < expires_at:
                # Remove MongoDB _id
                session_data.pop("_id", None)
                return session_data
    except:
        pass
    
    return None

def clear_session(user_id: str = None, session_token: str = None):
    """Clear session"""
    # Clear file
    if user_id:
        session_file = get_session_file_path(user_id)
        if session_file.exists():
            session_file.unlink()
    
    # Clear MongoDB
    try:
        db = get_db()
        query = {}
        if user_id:
            query["user_id"] = user_id
        if session_token:
            query["token"] = session_token
        db.sessions.delete_many(query)
    except:
        pass

def restore_session_from_storage():
    """Try to restore session from storage"""
    # Check query params first (if present)
    try:
        query_params = st.query_params
        user_id = query_params.get("user", None)
        session_token = query_params.get("token", None)
        
        if user_id:
            session_data = validate_session(session_token, user_id)
            if session_data:
                return session_data.get("user_id"), session_data.get("token")
    except:
        pass
    
    # Check all session files (for same browser/device)
    # Get the most recent valid session
    session_dir = get_session_file_path()
    if session_dir.exists():
        sessions = []
        for session_file in session_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    expires_at = datetime.fromisoformat(session_data.get("expires_at", "2000-01-01"))
                    if datetime.now() < expires_at:
                        created_at = datetime.fromisoformat(session_data.get("created_at", "2000-01-01"))
                        sessions.append((created_at, session_data))
            except:
                continue
        
        # Return most recent session
        if sessions:
            sessions.sort(key=lambda x: x[0], reverse=True)
            _, session_data = sessions[0]
            return session_data.get("user_id"), session_data.get("token")
    
    return None, None

