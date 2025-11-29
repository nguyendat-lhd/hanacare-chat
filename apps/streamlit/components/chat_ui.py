"""
Chat UI Components
Enhanced chat interface components
"""
import streamlit as st

def render_message_with_chart(message: dict):
    """
    Render a chat message with optional chart
    
    Args:
        message: Dictionary with 'role', 'content', and optionally 'chart_data'
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    chart_data = message.get("chart_data")
    
    with st.chat_message(role):
        st.write(content)
        if chart_data:
            # Chart rendering would be handled by charts.py
            pass

