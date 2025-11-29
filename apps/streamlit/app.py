"""
HealthSync AI - Main Streamlit Application
Chat with your health data using AI
"""
import streamlit as st
from utils.auth import check_auth, login_page
from utils.mcp_client import MCPHealthClient
import asyncio

# Page config
st.set_page_config(
    page_title="HealthSync AI",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "session_token" not in st.session_state:
    st.session_state.session_token = None
if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = None
if "health_data_loaded" not in st.session_state:
    st.session_state.health_data_loaded = False
if "mcp_connected" not in st.session_state:
    st.session_state.mcp_connected = False

# Try to restore session from storage
if not st.session_state.authenticated:
    from utils.session import restore_session_from_storage, validate_session
    user_id, session_token = restore_session_from_storage()
    if user_id:
        # Validate session
        session_data = validate_session(session_token, user_id)
        if session_data:
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.session_token = session_token
            # Optionally update query params (but don't require them)
            try:
                if "user" not in st.query_params:
                    st.query_params["user"] = user_id
                if session_token and "token" not in st.query_params:
                    st.query_params["token"] = session_token
            except:
                pass  # Query params update is optional

# Authentication
if not st.session_state.authenticated:
    login_page()
else:
    # Main app sidebar
    with st.sidebar:
        st.title("🍎 HealthSync AI")
        st.success(f"✅ Logged in as: **{st.session_state.user_id}**")
        
        if st.button("🚪 Logout", width='stretch'):
            # Cleanup MCP client
            if st.session_state.get("mcp_client"):
                try:
                    asyncio.run(st.session_state.mcp_client.close())
                except:
                    pass
            # Clear session
            from utils.session import clear_session
            clear_session(st.session_state.user_id, st.session_state.session_token)
            # Clear session state
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.session_token = None
            st.session_state.mcp_client = None
            st.session_state.health_data_loaded = False
            st.session_state.mcp_connected = False
            # Clear query params
            st.query_params.clear()
            st.rerun()
        
        st.divider()
        
        # Check data status
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        user_id = st.session_state.user_id
        storage_path = project_root / "storage" / "user_data" / user_id
        csv_files = list(storage_path.glob("*.csv")) if storage_path.exists() else []
        
        if len(csv_files) > 0:
            st.success(f"✅ Health data loaded ({len(csv_files)} files)")
            if any("sample" in str(f).lower() for f in csv_files) or len(csv_files) <= 4:
                st.info("💡 Using sample data. Upload real data in **Upload** page.")
        else:
            st.info("💡 Sample data will be auto-generated when you use **Chat** page")
        
        # MCP connection status
        if st.session_state.get("mcp_connected"):
            st.success("✅ MCP Server connected")
        else:
            st.warning("⚠️ MCP Server not connected")
    
    # Main content
    st.title("🍎 HealthSync AI")
    st.markdown("### Chat with Your Health Data")
    
    st.markdown("""
    Welcome to HealthSync AI! This application allows you to:
    
    - 📤 **Upload** your health data from Apple Health (via Simple Health Export CSV)
    - 💬 **Chat** with your data using natural language
    - 📊 **Visualize** your health metrics with interactive charts
    
    **Get Started:**
    1. Go to the **Upload** page to upload your health data ZIP file
    2. Visit the **Chat** page to start asking questions
    3. Check the **Dashboard** for visual overviews
    """)
    
    # Initialize MCP client
    if st.session_state.mcp_client is None:
        try:
            with st.spinner("Connecting to MCP Server..."):
                client = MCPHealthClient()
                # Try to connect
                try:
                    connection_result = asyncio.run(client.connect())
                    if connection_result:
                        st.session_state.mcp_client = client
                        st.session_state.mcp_connected = True
                        st.success("✅ Connected to MCP Server")
                    else:
                        st.warning("⚠️ MCP Server connection failed")
                        st.info("You can still use the app, but AI features may be limited")
                        st.session_state.mcp_client = client
                        st.session_state.mcp_connected = False
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    st.warning(f"⚠️ MCP Server connection failed: {str(e)}")
                    with st.expander("🔍 Error Details", expanded=False):
                        st.code(error_details)
                    st.info("You can still use the app, but AI features may be limited")
                    st.session_state.mcp_client = client
                    st.session_state.mcp_connected = False
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            st.error(f"Failed to initialize MCP Client: {str(e)}")
            with st.expander("🔍 Error Details", expanded=False):
                st.code(error_details)
            st.info("Make sure the MCP Server is running. The app will use a fallback client.")
    
    # Quick stats
    if st.session_state.health_data_loaded:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Status", "Ready")
        with col2:
            st.metric("Data", "Loaded")
        with col3:
            st.metric("AI", "Connected" if st.session_state.mcp_connected else "Offline")
        with col4:
            st.metric("User", st.session_state.user_id)

