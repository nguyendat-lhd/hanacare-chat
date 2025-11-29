"""
Chat Page - AI Chatbot Interface
Ask questions about your health data in natural language
"""
import streamlit as st
import json
import asyncio
from utils.mcp_client import MCPHealthClient
from components.charts import render_chart_from_data
from utils.db import save_chat_message, get_chat_history
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Chat - HealthSync AI",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Chat with Your Health Data")

if not st.session_state.get("authenticated"):
    st.warning("⚠️ Please login first!")
    st.stop()

if not st.session_state.get("health_data_loaded"):
    st.warning("⚠️ Please upload your health data first!")
    st.info("Go to the **Upload** page to upload your ZIP file")
    st.stop()

user_id = st.session_state.user_id
mcp_client = st.session_state.get("mcp_client")

if not mcp_client:
    st.error("❌ MCP Client not initialized. Please go to the main page first.")
    st.stop()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.warning("⚠️ OPENAI_API_KEY not set. AI features will be limited.")
    openai_client = None
else:
    openai_client = OpenAI(api_key=openai_api_key)

# Load chat history
chat_history = get_chat_history(user_id)

# Display chat history
for msg in chat_history[-20:]:  # Show last 20 messages
    role = msg.get("role", "user")
    content = msg.get("content", "")
    chart_data = msg.get("chart_data")
    
    with st.chat_message(role):
        st.write(content)
        if chart_data and role == "assistant":
            try:
                chart = render_chart_from_data(chart_data)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering chart: {e}")

# Chat input
if prompt := st.chat_input("Ask about your health data... (e.g., 'How many steps did I take last week?')"):
    # Add user message to UI
    with st.chat_message("user"):
        st.write(prompt)
    
    # Save user message
    save_chat_message(user_id, "user", prompt)
    
    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Step 1: Get schema
                schema_result = asyncio.run(
                    mcp_client.call_tool("health_schema", {"user_id": user_id})
                )
                
                if isinstance(schema_result, str):
                    schema_result = json.loads(schema_result)
                
                # Step 2: Generate SQL from natural language
                if openai_client:
                    sql_prompt = f"""You are a SQL expert. Based on this health data schema:
                    
{json.dumps(schema_result, indent=2)}

User question: {prompt}

Generate a SQL query to answer this question. Only return the SQL query, nothing else. Do not include markdown code blocks, just the SQL query.

Available tables: {', '.join(schema_result.get('tables', {}).keys()) if isinstance(schema_result, dict) else 'unknown'}
"""
                    
                    sql_response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",  # Using mini for cost efficiency
                        messages=[{"role": "user", "content": sql_prompt}],
                        temperature=0.1
                    )
                    sql_query = sql_response.choices[0].message.content.strip()
                    
                    # Clean SQL query (remove markdown if present)
                    if sql_query.startswith("```sql"):
                        sql_query = sql_query[6:]
                    if sql_query.startswith("```"):
                        sql_query = sql_query[3:]
                    if sql_query.endswith("```"):
                        sql_query = sql_query[:-3]
                    sql_query = sql_query.strip()
                    
                    st.code(sql_query, language="sql")
                else:
                    # Fallback: simple SQL generation
                    sql_query = f"SELECT * FROM steps LIMIT 10"  # Placeholder
                    st.warning("Using placeholder SQL (OpenAI not configured)")
                
                # Step 3: Execute query via MCP
                query_result = asyncio.run(
                    mcp_client.call_tool("health_query", {
                        "sql": sql_query,
                        "user_id": user_id
                    })
                )
                
                if isinstance(query_result, str):
                    query_result = json.loads(query_result)
                
                # Step 4: Generate natural language response
                if openai_client and query_result.get("data"):
                    response_prompt = f"""User asked: {prompt}

Query result (first 10 rows):
{json.dumps(query_result.get('data', [])[:10], indent=2)}

Total rows: {query_result.get('row_count', 0)}

Provide a helpful, natural language answer. Be concise and highlight key insights. If there's data, mention specific numbers and trends.
"""
                    
                    ai_response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": response_prompt}],
                        temperature=0.7
                    )
                    answer = ai_response.choices[0].message.content
                else:
                    # Fallback response
                    if query_result.get("data"):
                        answer = f"I found {query_result.get('row_count', 0)} records. Here's the data:\n\n{json.dumps(query_result.get('data', [])[:5], indent=2)}"
                    else:
                        answer = f"Query executed. Result: {json.dumps(query_result, indent=2)}"
                
                st.write(answer)
                
                # Step 5: Render chart if data exists
                if query_result.get("data") and len(query_result["data"]) > 0:
                    try:
                        chart = render_chart_from_data(query_result["data"])
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                            save_chat_message(
                                user_id,
                                "assistant",
                                answer,
                                chart_data=query_result["data"]
                            )
                        else:
                            save_chat_message(user_id, "assistant", answer)
                    except Exception as e:
                        st.warning(f"Could not render chart: {e}")
                        save_chat_message(user_id, "assistant", answer)
                else:
                    save_chat_message(user_id, "assistant", answer)
            
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                save_chat_message(user_id, "assistant", error_msg)
                st.exception(e)

# Example questions
with st.expander("💡 Example Questions"):
    st.markdown("""
    Try asking:
    - "How many steps did I take last week?"
    - "What was my average heart rate yesterday?"
    - "Show me my sleep data for the past 7 days"
    - "How many workouts did I do this month?"
    - "What's my step count trend over the last month?"
    """)

