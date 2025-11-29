"""
Authentication Utilities
Simple authentication for Streamlit app
"""
import streamlit as st
from utils.db import get_db
from datetime import datetime
import hashlib

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth(user_id: str, password: str) -> bool:
    """Check if user credentials are valid"""
    try:
        db = get_db()
        user = db.users.find_one({"user_id": user_id})
        if user and user.get("password_hash") == hash_password(password):
            return True
        return False
    except Exception as e:
        print(f"Auth error: {e}")
        return False

def create_user(user_id: str, password: str, email: str = "") -> bool:
    """Create new user"""
    try:
        db = get_db()
        # Check if user exists
        if db.users.find_one({"user_id": user_id}):
            return False
        
        user = {
            "user_id": user_id,
            "password_hash": hash_password(password),
            "email": email,
            "created_at": datetime.now()
        }
        db.users.insert_one(user)
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def login_page():
    """Render login/signup page"""
    st.title("🍎 HealthSync AI")
    st.markdown("### Login to Your Health Dashboard")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        user_id = st.text_input("User ID", key="login_user_id")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", width='stretch'):
            if user_id and password:
                if check_auth(user_id, password):
                    from utils.session import create_session
                    # Create session
                    session_token = create_session(user_id)
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.session_state.session_token = session_token
                    # Optionally set query params (for URL persistence)
                    try:
                        st.query_params["user"] = user_id
                        st.query_params["token"] = session_token
                    except:
                        pass  # Query params are optional
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
            else:
                st.warning("⚠️ Please enter both user ID and password")
    
    with tab2:
        st.subheader("Create Account")
        new_user_id = st.text_input("User ID", key="signup_user_id")
        new_email = st.text_input("Email (optional)", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        if st.button("Sign Up", width='stretch'):
            if new_user_id and new_password:
                if new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(new_password) < 4:
                    st.error("❌ Password must be at least 4 characters")
                else:
                    if create_user(new_user_id, new_password, new_email):
                        st.success("✅ Account created! Please login.")
                    else:
                        st.error("❌ User ID already exists")
                        st.info("💡 **Options:**\n"
                               "- Try a different User ID\n"
                               "- If you forgot your password, you can delete the user using:\n"
                               "  `python scripts/delete_user.py <user_id>`")
            else:
                st.warning("⚠️ Please fill in all required fields")

