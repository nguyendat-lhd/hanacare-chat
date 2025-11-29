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

if not st.session_state.get("health_data_loaded"):
    st.warning("⚠️ Please upload your health data first!")
    st.info("Go to the **Upload** page to upload your ZIP file")
    st.stop()

user_id = st.session_state.user_id
# Get project root (3 levels up from pages/)
project_root = Path(__file__).parent.parent.parent.parent
storage_path = project_root / "storage" / "user_data" / user_id

if not storage_path.exists():
    st.error("❌ No data directory found")
    st.stop()

# Find CSV files
csv_files = list(storage_path.glob("*.csv"))

if not csv_files:
    st.warning("⚠️ No CSV files found")
    st.stop()

# Connect to DuckDB
conn = duckdb.connect()

try:
    # Register CSV files as tables
    for csv_file in csv_files:
        table_name = csv_file.stem
        try:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} AS 
                SELECT * FROM read_csv_auto('{csv_file}')
            """)
        except Exception as e:
            st.warning(f"Could not load {table_name}: {e}")
    
    # Get available tables
    tables = [f.stem for f in csv_files]
    
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
            steps_df = conn.execute(f"SELECT * FROM {steps_table} LIMIT 1000").df()
            
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
                hr_df = conn.execute(f"SELECT * FROM {hr_table} LIMIT 1000").df()
                
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
            df = conn.execute(f"SELECT * FROM {selected_table} LIMIT 100").df()
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

