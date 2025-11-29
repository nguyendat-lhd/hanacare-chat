"""
Chat Page - AI Chatbot Interface
Ask questions about your health data in natural language
"""
import streamlit as st
import json
import asyncio
import pandas as pd
from components.charts import render_chart_from_data
from utils.db import save_chat_message, get_chat_history, clear_chat_history
# Using direct query - no MCP server needed
import google.generativeai as genai
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

# Auto-generate sample data ONLY if no uploaded data exists
user_id = st.session_state.user_id
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
storage_path = project_root / "storage" / "user_data" / user_id

if not st.session_state.get("health_data_loaded"):
    # Check if user has uploaded data (has metadata in DB)
    from utils.db import get_file_metadata
    uploaded_files = get_file_metadata(user_id)
    has_uploaded_data = len(uploaded_files) > 0
    
    # Check existing CSV files
    csv_files = list(storage_path.glob("*.csv")) if storage_path.exists() else []
    
    # Only generate sample data if:
    # 1. No uploaded data in DB (no metadata)
    # 2. No CSV files exist
    if not has_uploaded_data and len(csv_files) == 0:
        # Generate sample data
        from utils.sample_data import generate_sample_data
        with st.spinner("🎲 Generating sample data for demo..."):
            try:
                result = generate_sample_data(user_id, storage_path)
                st.session_state.health_data_loaded = True
                st.success(f"✅ Generated sample data: {result.get('steps', 0)} steps, {result.get('heart_rate', 0)} heart rate readings, {result.get('sleep', 0)} sleep records, {result.get('workouts', 0)} workouts")
                st.info("💡 This is **sample data** for demo. Upload your real data in the **Upload** page to use your actual health data.")
                st.rerun()  # Reload to ensure data is available
            except Exception as e:
                st.error(f"❌ Error generating sample data: {e}")
                import traceback
                with st.expander("Error details"):
                    st.code(traceback.format_exc())
                st.stop()
    else:
        # Data exists (either uploaded or sample), just mark as loaded
        st.session_state.health_data_loaded = True
        if has_uploaded_data:
            st.info(f"📊 Using your uploaded data ({len(csv_files)} file(s)). You can upload new data in the **Upload** page.")
        else:
            st.info(f"📊 Found {len(csv_files)} data file(s). You can upload new data in the **Upload** page.")

# Always use direct query - query CSV files directly + Gemini AI for responses
from utils.direct_query import get_schema_direct, execute_query_direct
st.info("ℹ️ Using direct CSV query + Gemini AI - ready to chat!")

# Initialize Gemini AI client
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.warning("⚠️ GEMINI_API_KEY not set. AI features will be limited.")
    gemini_client = None
else:
    genai.configure(api_key=gemini_api_key)
    gemini_client = genai.GenerativeModel("gemini-2.5-flash")

# Clear chat history button
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🗑️ Clear History", help="Clear all chat history"):
        deleted_count = clear_chat_history(user_id)
        if deleted_count > 0:
            st.success(f"✅ Cleared {deleted_count} message(s)")
            st.rerun()
        else:
            st.info("No messages to clear")

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
                    st.plotly_chart(chart, width='stretch')
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
                # Step 1: Get schema directly from CSV files (always use direct query)
                schema_result = get_schema_direct(user_id)
                
                if isinstance(schema_result, str):
                    schema_result = json.loads(schema_result)
                
                # Step 2: Generate SQL from natural language
                if gemini_client:
                    # Build table info for AI
                    tables_info = []
                    if isinstance(schema_result, dict) and schema_result.get('tables'):
                        for orig_name, table_info in schema_result['tables'].items():
                            if isinstance(table_info, dict):
                                table_name = table_info.get('table_name', orig_name)
                                escaped = table_info.get('escaped_name', f'"{table_name}"')
                                tables_info.append(f"{table_name} (use in SQL: {escaped})")
                    
                    sql_prompt = f"""You are a SQL expert. Based on this health data schema:

{json.dumps(schema_result, indent=2)}

User question: {prompt}

IMPORTANT RULES:
1. Use the EXACT table names as shown in the schema (they may contain dashes and special characters)
2. When querying multiple tables, you MUST use JOINs, not comma-separated tables in FROM
3. Always qualify column names with table names when querying multiple tables (e.g., table1.value, table2.value)
4. If you need data from multiple tables, use UNION ALL or separate queries, not comma-separated FROM
5. Each table has a "value" column - you MUST qualify it with table name when multiple tables are involved
6. **CRITICAL: The "value" column is stored as VARCHAR in CSV files, but contains numeric data**
   - **You MUST cast it to DOUBLE when using in aggregate functions: CAST(value AS DOUBLE) or CAST(table.value AS DOUBLE)**
   - Example: AVG(CAST(value AS DOUBLE)), SUM(CAST(t1.value AS DOUBLE))
   - Example: AVG(value) is WRONG, use AVG(CAST(value AS DOUBLE)) instead
6. **CRITICAL: Use DuckDB date functions and casting:**
   - Use: CURRENT_DATE - INTERVAL '7 days' (NOT DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY))
   - Use: CURRENT_DATE - INTERVAL '1 month' (NOT DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH))
   - Use: CURRENT_TIMESTAMP - INTERVAL '1 hour' (NOT DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 HOUR))
   - Date arithmetic: date_column - INTERVAL 'N days', date_column + INTERVAL 'N days'
   - Extract: EXTRACT(day FROM date_column), EXTRACT(month FROM date_column), EXTRACT(year FROM date_column)
   - Date formatting: strftime(date_column, '%Y-%m-%d')
   - **IMPORTANT: Date columns (startDate, endDate, date, timestamp) are stored as VARCHAR in CSV files**
   - **These columns may contain timezone info (e.g., "2019-02-12 10:15:05 +0000")**
   - **Use TRY_CAST with TIMESTAMPTZ to handle timezone-aware timestamps: TRY_CAST(column AS TIMESTAMPTZ)**
   - Example: WHERE TRY_CAST(startDate AS TIMESTAMPTZ) >= CURRENT_DATE - INTERVAL '7 days'

Available tables:
{chr(10).join(tables_info) if tables_info else 'No tables available'}

Example of CORRECT query with date filtering:
SELECT * FROM "Table1" 
WHERE TRY_CAST(startDate AS TIMESTAMPTZ) >= CURRENT_DATE - INTERVAL '7 days'

Note: Always cast date columns (startDate, endDate, date, timestamp) to TIMESTAMPTZ using TRY_CAST before comparing with CURRENT_DATE or date literals. This handles timezone-aware timestamps gracefully.

Example of WRONG query (DO NOT DO THIS):
SELECT * FROM "Table1" 
WHERE startDate >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)  -- This will fail in DuckDB

Example of CORRECT query with multiple tables:
SELECT t1.value as heart_rate, t2.value as steps
FROM "Table1" t1
JOIN "Table2" t2 ON t1.date = t2.date

Example of WRONG query (DO NOT DO THIS):
SELECT value FROM "Table1", "Table2"  -- This causes ambiguous column error

Generate a SQL query to answer this question. Use the exact table names from the schema above.
Use DuckDB date syntax (subtraction with INTERVAL, not DATE_SUB function).
Only return the SQL query, nothing else. Do not include markdown code blocks, just the SQL query.
"""
                    
                    try:
                        sql_response = gemini_client.generate_content(sql_prompt)
                        # Extract SQL query safely
                        if sql_response and sql_response.text:
                            sql_query = sql_response.text.strip()
                        else:
                            raise ValueError("No response from Gemini API for SQL generation")
                    except Exception as gemini_error:
                        st.error(f"❌ Lỗi khi tạo SQL query từ Gemini API: {str(gemini_error)}")
                        # Fallback to simple query
                        sql_query = f"SELECT * FROM steps LIMIT 10"
                        st.warning("⚠️ Sử dụng SQL query mặc định do lỗi API")
                    
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
                    st.warning("Using placeholder SQL (Gemini not configured)")
                
                # Step 3: Execute query directly on CSV files (always use direct query)
                query_result = execute_query_direct(sql_query, user_id)
                
                if isinstance(query_result, str):
                    query_result = json.loads(query_result)
                
                # Debug: Check query result structure
                if "error" in query_result:
                    st.error(f"Query error: {query_result['error']}")
                    st.json(query_result)
                    st.stop()  # Stop execution instead of return
                
                # Debug: Log query result structure (for troubleshooting)
                with st.expander("🔍 Debug: Query Result Structure", expanded=False):
                    st.json(query_result)
                    st.write(f"Has 'data' key: {'data' in query_result}")
                    st.write(f"Data type: {type(query_result.get('data'))}")
                    st.write(f"Data value: {query_result.get('data')}")
                    st.write(f"Row count: {query_result.get('row_count', 'N/A')}")
                    st.write(f"Success: {query_result.get('success', 'N/A')}")
                
                # Step 4: Generate natural language response with Gemini AI
                # Check if we have data to analyze
                data_list = query_result.get("data")
                row_count = query_result.get("row_count", 0)
                success = query_result.get("success", False)
                
                has_data = False
                answer = None
                
                # Check multiple ways to determine if we have data
                if data_list is not None:
                    if isinstance(data_list, list):
                        has_data = len(data_list) > 0
                    elif isinstance(data_list, dict):
                        has_data = len(data_list) > 0
                
                # If data_list check failed but row_count > 0, we likely have data
                if not has_data and row_count > 0:
                    has_data = True
                    if not data_list or (isinstance(data_list, list) and len(data_list) == 0):
                        st.warning(f"⚠️ Query returned {row_count} rows but data list is empty. This might be a data format issue.")
                        if "columns" in query_result:
                            st.info(f"Columns available: {query_result.get('columns')}")
                
                # Final check: if success=True and row_count > 0, we should have data
                if success and row_count > 0 and not has_data:
                    has_data = True
                    st.info(f"✅ Query thành công với {row_count} bản ghi. Đang xử lý dữ liệu...")
                
                # Generate AI response with Gemini
                if gemini_client and has_data:
                    # Get schema context for better understanding
                    schema_context = ""
                    if isinstance(schema_result, dict) and schema_result.get('tables'):
                        schema_context = "\n\nAvailable health data tables and their meanings:\n"
                        for table_name, table_info in schema_result['tables'].items():
                            if isinstance(table_info, dict):
                                metric_type = table_name
                                if "HeartRate" in table_name:
                                    metric_type = "Heart Rate (beats per minute)"
                                elif "Steps" in table_name or "DistanceWalkingRunning" in table_name:
                                    metric_type = "Steps / Walking Distance"
                                elif "ActiveEnergyBurned" in table_name:
                                    metric_type = "Active Energy Burned (calories)"
                                elif "BasalEnergyBurned" in table_name:
                                    metric_type = "Basal Energy Burned (calories)"
                                elif "Sleep" in table_name:
                                    metric_type = "Sleep Data"
                                elif "BodyMass" in table_name or "Weight" in table_name:
                                    metric_type = "Body Weight (kg)"
                                elif "Height" in table_name:
                                    metric_type = "Height (cm)"
                                elif "VO2Max" in table_name:
                                    metric_type = "VO2 Max (cardiorespiratory fitness)"
                                elif "BodyFatPercentage" in table_name:
                                    metric_type = "Body Fat Percentage (%)"
                                elif "RestingHeartRate" in table_name:
                                    metric_type = "Resting Heart Rate (bpm)"
                                elif "FlightsClimbed" in table_name:
                                    metric_type = "Flights Climbed"
                                else:
                                    metric_type = table_name
                                
                                columns = table_info.get('columns', [])
                                schema_context += f"- {table_name}: {metric_type}\n"
                                if columns:
                                    schema_context += f"  Columns: {', '.join(columns[:5])}\n"
                    
                    # Build data summary
                    data_rows = query_result.get('data', [])
                    columns = query_result.get('columns', [])
                    data_summary = ""
                    
                    if data_rows and len(data_rows) > 0:
                        if isinstance(data_rows[0], dict):
                            columns = list(data_rows[0].keys())
                            data_summary = f"\nColumns in result: {', '.join(columns)}\n\n"
                            data_summary += "Sample data (first 10 rows):\n"
                            data_summary += json.dumps(data_rows[:10], indent=2)
                        else:
                            data_summary = json.dumps(data_rows[:10], indent=2)
                    elif columns:
                        data_summary = f"\nColumns in result: {', '.join(columns)}\n"
                        data_summary += f"Total rows: {row_count}\n"
                        data_summary += "Note: Data rows are not available in the response, but the query returned results."
                    elif row_count > 0:
                        data_summary = f"\nQuery returned {row_count} rows.\n"
                        data_summary += "Note: Detailed data is not available in the response format."
                    
                    response_prompt = f"""You are a health data assistant helping users understand their Apple Health data.

User's question: {prompt}

{schema_context}

Query executed successfully. Results:
{data_summary}

Total rows returned: {query_result.get('row_count', len(data_rows))}

SQL query used: {sql_query}

Please provide a helpful, natural language answer in Vietnamese that:
1. Directly answers the user's question
2. Mentions specific numbers and values from the data
3. Highlights key insights or trends if applicable
4. Explains what the data means in the context of health and fitness
5. Be concise but informative

If the data shows health metrics, interpret them appropriately (e.g., heart rate ranges, step counts, etc.).
"""
                    
                    try:
                        ai_response = gemini_client.generate_content(response_prompt)
                        if ai_response and ai_response.text:
                            answer = ai_response.text.strip()
                            if not answer or answer.strip() == "":
                                answer = "Xin lỗi, tôi không thể tạo phản hồi. Vui lòng thử lại."
                        else:
                            answer = "Không nhận được phản hồi từ AI. Vui lòng thử lại."
                    except Exception as gemini_error:
                        st.error(f"❌ Lỗi khi gọi Gemini API: {str(gemini_error)}")
                        if data_rows and len(data_rows) > 0:
                            answer = f"Tôi tìm thấy {row_count} bản ghi. Dữ liệu:\n\n{json.dumps(data_rows[:5], indent=2, ensure_ascii=False)}"
                        else:
                            answer = f"Truy vấn thành công với {row_count} bản ghi, nhưng không thể tạo phản hồi tự động."
                elif gemini_client and query_result.get("success") and not has_data:
                    actual_row_count = query_result.get("row_count", 0)
                    if actual_row_count > 0:
                        st.info(f"⚠️ Phát hiện {actual_row_count} bản ghi nhưng format dữ liệu có thể không đúng. Đang xử lý...")
                        response_prompt = f"""User asked: {prompt}

SQL query executed: {sql_query}

The query executed successfully and returned {actual_row_count} rows, but the data format might be different.

Please provide a helpful response in Vietnamese explaining:
1. The query found {actual_row_count} records
2. But the data format might need adjustment
3. Suggest the user check their query or try a different question

Be positive and helpful.
"""
                        try:
                            ai_response = gemini_client.generate_content(response_prompt)
                            if ai_response and ai_response.text:
                                answer = ai_response.text.strip()
                            else:
                                answer = f"Truy vấn tìm thấy {actual_row_count} bản ghi, nhưng format dữ liệu có thể cần điều chỉnh."
                        except Exception as gemini_error:
                            st.warning(f"⚠️ Lỗi khi gọi Gemini API: {str(gemini_error)}")
                            answer = f"Truy vấn tìm thấy {actual_row_count} bản ghi, nhưng format dữ liệu có thể cần điều chỉnh. Vui lòng thử câu hỏi khác."
                    else:
                        response_prompt = f"""User asked: {prompt}

SQL query executed: {sql_query}

The query executed successfully but returned no data (0 rows).

Please explain to the user in Vietnamese that:
1. The query ran successfully
2. But there is no data matching their criteria
3. Suggest they might need to check their data or adjust their question
"""
                        try:
                            ai_response = gemini_client.generate_content(response_prompt)
                            if ai_response and ai_response.text:
                                answer = ai_response.text.strip()
                            else:
                                answer = "Truy vấn đã thực hiện thành công nhưng không có dữ liệu trả về phù hợp với tiêu chí."
                        except Exception as gemini_error:
                            st.warning(f"⚠️ Lỗi khi gọi Gemini API: {str(gemini_error)}")
                            answer = "Truy vấn đã thực hiện thành công nhưng không có dữ liệu trả về phù hợp với tiêu chí. Vui lòng thử câu hỏi khác hoặc kiểm tra lại dữ liệu."
                else:
                    # Fallback response (when Gemini is not available)
                    if query_result.get("data") and len(query_result.get("data", [])) > 0:
                        answer = f"Tôi tìm thấy {query_result.get('row_count', 0)} bản ghi. Dữ liệu:\n\n{json.dumps(query_result.get('data', [])[:5], indent=2, ensure_ascii=False)}"
                    elif query_result.get("success") and row_count > 0:
                        answer = f"Truy vấn thành công với {row_count} bản ghi, nhưng dữ liệu chi tiết không có sẵn."
                    elif query_result.get("success"):
                        answer = "Truy vấn đã thực hiện thành công nhưng không có dữ liệu trả về phù hợp với tiêu chí."
                    else:
                        error_msg = query_result.get('error', 'Unknown error')
                        answer = f"Lỗi truy vấn: {error_msg}"
                
                # Ensure answer is always set
                if not answer:
                    answer = "Không thể tạo phản hồi. Vui lòng thử lại."
                
                # Display answer text
                st.write(answer)
                
                # Get query result info for data display
                data_rows = query_result.get("data")
                actual_row_count = query_result.get("row_count", 0)
                query_success = query_result.get("success", False)
                
                # Check if we have data to display
                has_data_rows = False
                if data_rows is not None:
                    if isinstance(data_rows, list):
                        has_data_rows = len(data_rows) > 0
                    elif isinstance(data_rows, dict):
                        has_data_rows = len(data_rows) > 0
                
                # Display data table directly if we have data
                if has_data_rows and isinstance(data_rows, list) and len(data_rows) > 0:
                    st.markdown("### 📊 Dữ liệu từ CSV:")
                    try:
                        df = pd.DataFrame(data_rows)
                        st.dataframe(df, width='stretch', use_container_width=False)
                        if len(data_rows) > 20:
                            st.caption(f"Hiển thị tất cả {len(data_rows)} bản ghi. Cuộn để xem thêm.")
                    except Exception as df_error:
                        st.warning(f"⚠️ Không thể hiển thị dạng bảng: {str(df_error)}")
                        # Fallback to JSON
                        if len(data_rows) <= 20:
                            st.json(data_rows)
                        else:
                            st.json(data_rows[:20])
                            st.info(f"... và {len(data_rows) - 20} bản ghi khác")
                elif actual_row_count > 0:
                    st.info(f"ℹ️ Query trả về {actual_row_count} bản ghi nhưng dữ liệu chi tiết không có sẵn.")
                
                # Display raw data from CSV files - always show if query was executed (detailed view)
                with st.expander("📊 Xem chi tiết dữ liệu từ CSV", expanded=False):
                    # Get data from query result
                    data_rows = query_result.get("data")
                    actual_row_count = query_result.get("row_count", 0)
                    query_success = query_result.get("success", False)
                    
                    st.write(f"**Tổng số bản ghi:** {actual_row_count}")
                    st.write(f"**Trạng thái query:** {'✅ Thành công' if query_success else '❌ Lỗi'}")
                    
                    # Check if we have data to display
                    has_data_rows = False
                    if data_rows is not None:
                        if isinstance(data_rows, list):
                            has_data_rows = len(data_rows) > 0
                        elif isinstance(data_rows, dict):
                            has_data_rows = len(data_rows) > 0
                    
                    if has_data_rows:
                        # Display as table
                        try:
                            if isinstance(data_rows, list) and len(data_rows) > 0:
                                df = pd.DataFrame(data_rows)
                                st.dataframe(df, width='stretch', use_container_width=False)
                                
                                # Also show as JSON for detailed view
                                with st.expander("📋 Xem dữ liệu dạng JSON"):
                                    st.json(data_rows[:50])  # Show first 50 rows
                                    if len(data_rows) > 50:
                                        st.info(f"... và {len(data_rows) - 50} bản ghi khác")
                            else:
                                st.json(data_rows)
                        except Exception as df_error:
                            st.warning(f"⚠️ Không thể hiển thị dạng bảng: {str(df_error)}")
                            # Fallback to JSON
                            if isinstance(data_rows, list):
                                st.json(data_rows[:20])
                            else:
                                st.json(data_rows)
                    elif actual_row_count > 0:
                        # Query returned rows but data list is empty or None
                        st.info(f"ℹ️ Query trả về {actual_row_count} bản ghi nhưng dữ liệu chi tiết không có sẵn.")
                        if "columns" in query_result:
                            st.write(f"**Các cột có sẵn:** {', '.join(query_result.get('columns', []))}")
                        # Show full query result for debugging
                        with st.expander("🔍 Xem chi tiết query result"):
                            st.json(query_result)
                    elif query_success:
                        st.info("ℹ️ Query thực hiện thành công nhưng không có dữ liệu trả về.")
                        with st.expander("🔍 Xem chi tiết query result"):
                            st.json(query_result)
                    else:
                        # Query failed
                        error_msg = query_result.get('error', 'Unknown error')
                        st.error(f"❌ Query lỗi: {error_msg}")
                        with st.expander("🔍 Xem chi tiết query result"):
                            st.json(query_result)
                
                # Step 5: Render chart if data exists
                if query_result.get("data") and len(query_result["data"]) > 0:
                    try:
                        chart = render_chart_from_data(query_result["data"])
                        if chart:
                            st.plotly_chart(chart, width='stretch')
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

