"""
Health Cards Component
Display summary cards for health metrics
"""
import streamlit as st
import pandas as pd
import duckdb
from datetime import datetime, timedelta

def render_health_cards(conn: duckdb.DuckDBPyConnection, tables: list):
    """
    Render health summary cards
    
    Args:
        conn: DuckDB connection
        tables: List of available table names
    """
    st.subheader("📊 Health Summary")
    
    cols = st.columns(4)
    
    # Try to get steps data
    steps_table = next((t for t in tables if "step" in t.lower()), None)
    if steps_table:
        try:
            steps_df = conn.execute(f"SELECT * FROM {steps_table} LIMIT 1000").df()
            if not steps_df.empty:
                value_col = next((c for c in steps_df.columns if "value" in c.lower() or "count" in c.lower() or "step" in c.lower()), None)
                if value_col:
                    total_steps = steps_df[value_col].sum()
                    with cols[0]:
                        st.metric("Total Steps", f"{int(total_steps):,}")
        except:
            pass
    
    # Try to get heart rate data
    hr_table = next((t for t in tables if "heart" in t.lower() or "hr" in t.lower()), None)
    if hr_table:
        try:
            hr_df = conn.execute(f"SELECT * FROM {hr_table} LIMIT 1000").df()
            if not hr_df.empty:
                value_col = next((c for c in hr_df.columns if "value" in c.lower() or "rate" in c.lower() or "bpm" in c.lower()), None)
                if value_col:
                    avg_hr = hr_df[value_col].mean()
                    with cols[1]:
                        st.metric("Avg Heart Rate", f"{int(avg_hr)} bpm")
        except:
            pass
    
    # Data files count
    with cols[2]:
        st.metric("Data Tables", len(tables))
    
    # Total records
    try:
        total_records = 0
        for table in tables[:5]:  # Check first 5 tables
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            total_records += count
        with cols[3]:
            st.metric("Total Records", f"{total_records:,}")
    except:
        with cols[3]:
            st.metric("Total Records", "N/A")

