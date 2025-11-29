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
if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = None
if "health_data_loaded" not in st.session_state:
    st.session_state.health_data_loaded = False
if "mcp_connected" not in st.session_state:
    st.session_state.mcp_connected = False

# Authentication
if not st.session_state.authenticated:
    login_page()
else:
    # Main app sidebar
    with st.sidebar:
        st.title("🍎 HealthSync AI")
        st.success(f"✅ Logged in as: **{st.session_state.user_id}**")
        
        if st.button("🚪 Logout", use_container_width=True):
            # Cleanup
            if st.session_state.mcp_client:
                try:
                    asyncio.run(st.session_state.mcp_client.close())
                except:
                    pass
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.mcp_client = None
            st.session_state.health_data_loaded = False
            st.session_state.mcp_connected = False
            st.rerun()
        
        st.divider()
        
        # Check data status
        if st.session_state.health_data_loaded:
            st.success("✅ Health data loaded")
        else:
            st.warning("⚠️ No health data uploaded")
            st.info("Go to **Upload** page to upload your data")
        
        # MCP connection status
        if st.session_state.mcp_connected:
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
                    asyncio.run(client.connect())
                    st.session_state.mcp_client = client
                    st.session_state.mcp_connected = True
                    st.success("✅ Connected to MCP Server")
                except Exception as e:
                    st.warning(f"⚠️ MCP Server connection failed: {e}")
                    st.info("You can still use the app, but AI features may be limited")
                    st.session_state.mcp_client = client
                    st.session_state.mcp_connected = False
        except Exception as e:
            st.error(f"Failed to initialize MCP Client: {e}")
            st.info("Make sure the MCP Server is running")
    
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

