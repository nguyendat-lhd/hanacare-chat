"""
Dashboard Page - Health Metrics Overview
Visualize health data with charts and summary cards
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
from components.health_cards import render_health_cards

st.set_page_config(
    page_title="Dashboard - HealthSync AI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Health Dashboard")

if not st.session_state.get("authenticated"):
    st.warning("⚠️ Please login first!")
    st.stop()

# Auto-generate sample data if no data exists
user_id = st.session_state.user_id
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
storage_path = project_root / "storage" / "user_data" / user_id

if not st.session_state.get("health_data_loaded"):
    # Check if sample data exists or generate it
    csv_files = list(storage_path.glob("*.csv")) if storage_path.exists() else []
    
    if len(csv_files) == 0:
        # Generate sample data
        from utils.sample_data import generate_sample_data
        with st.spinner("🎲 Generating sample data for demo..."):
            try:
                result = generate_sample_data(user_id, storage_path)
                st.session_state.health_data_loaded = True
                st.success(f"✅ Generated sample data for demo")
            except Exception as e:
                st.error(f"❌ Error generating sample data: {e}")
                st.stop()
    else:
        st.session_state.health_data_loaded = True

# storage_path already defined above
if not storage_path.exists():
    storage_path.mkdir(parents=True, exist_ok=True)

# Find CSV files
csv_files = list(storage_path.glob("*.csv"))

if not csv_files:
    st.warning("⚠️ No CSV files found")
    st.stop()

# Connect to DuckDB
conn = duckdb.connect()

try:
    # Register CSV files as tables - keep original names
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root / "packages" / "mcp_server" / "tools"))
    from table_utils import escape_table_name
    
    for csv_file in csv_files:
        original_name = csv_file.stem
        # Keep original name, just escape it
        escaped_name = escape_table_name(original_name)
        try:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {escaped_name} AS 
                SELECT * FROM read_csv_auto('{csv_file}')
            """)
        except Exception as e:
            st.warning(f"Could not load {original_name} (normalized: {normalized_name}): {e}")
    
    # Get available tables (use original names)
    tables = [f.stem for f in csv_files]  # Keep original names
    
    # Health Cards
    render_health_cards(conn, tables)
    
    st.divider()
    
    # Charts section
    st.subheader("📈 Detailed Charts")
    
    # Try to find common health metrics
    if "steps" in tables or any("step" in t.lower() for t in tables):
        st.markdown("### 👣 Steps")
        try:
            steps_table = next((t for t in tables if "step" in t.lower()), tables[0])
            escaped_table = escape_table_name(steps_table)
            steps_df = conn.execute(f"SELECT * FROM {escaped_table} LIMIT 1000").df()
            
            if not steps_df.empty:
                # Try to find date and value columns
                date_col = next((c for c in steps_df.columns if "date" in c.lower() or "time" in c.lower()), None)
                value_col = next((c for c in steps_df.columns if "value" in c.lower() or "count" in c.lower() or "step" in c.lower()), None)
                
                if date_col and value_col:
                    steps_df[date_col] = pd.to_datetime(steps_df[date_col], errors='coerce')
                    steps_df = steps_df.sort_values(date_col)
                    fig = px.line(steps_df, x=date_col, y=value_col, title="Steps Over Time")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(steps_df.head(20))
        except Exception as e:
            st.warning(f"Could not plot steps: {e}")
    
    if "heart" in " ".join(t.lower() for t in tables) or "hr" in " ".join(t.lower() for t in tables):
        st.markdown("### ❤️ Heart Rate")
        try:
            hr_table = next((t for t in tables if "heart" in t.lower() or "hr" in t.lower()), None)
            if hr_table:
                escaped_table = escape_table_name(hr_table)
                hr_df = conn.execute(f"SELECT * FROM {escaped_table} LIMIT 1000").df()
                
                if not hr_df.empty:
                    date_col = next((c for c in hr_df.columns if "date" in c.lower() or "time" in c.lower()), None)
                    value_col = next((c for c in hr_df.columns if "value" in c.lower() or "rate" in c.lower() or "bpm" in c.lower()), None)
                    
                    if date_col and value_col:
                        hr_df[date_col] = pd.to_datetime(hr_df[date_col], errors='coerce')
                        hr_df = hr_df.sort_values(date_col)
                        fig = px.line(hr_df, x=date_col, y=value_col, title="Heart Rate Over Time")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(hr_df.head(20))
        except Exception as e:
            st.warning(f"Could not plot heart rate: {e}")
    
    # Data explorer
    st.divider()
    st.subheader("🔍 Data Explorer")
    
    selected_table = st.selectbox("Select a table to explore", tables)
    
    if selected_table:
        try:
            escaped_table = escape_table_name(selected_table)
            df = conn.execute(f"SELECT * FROM {escaped_table} LIMIT 100").df()
            st.dataframe(df, use_container_width=True)
            
            st.markdown(f"**Columns:** {', '.join(df.columns)}")
            st.markdown(f"**Rows shown:** {len(df)} (limited to 100)")
        except Exception as e:
            st.error(f"Error loading table: {e}")

except Exception as e:
    st.error(f"Error: {e}")
    st.exception(e)

finally:
    conn.close()

