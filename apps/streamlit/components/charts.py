"""
Chart Components
Render charts from health data
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def render_chart_from_data(data: list) -> go.Figure:
    """
    Automatically render appropriate chart from data
    
    Args:
        data: List of dictionaries with health data
    
    Returns:
        Plotly figure or None
    """
    if not data or len(data) == 0:
        return None
    
    try:
        df = pd.DataFrame(data)
        
        if df.empty:
            return None
        
        # Try to find date/time column
        date_col = None
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower() or "timestamp" in col.lower():
                date_col = col
                break
        
        # Try to find value column
        value_col = None
        for col in df.columns:
            if col != date_col and ("value" in col.lower() or "count" in col.lower() or 
                                   "step" in col.lower() or "rate" in col.lower() or
                                   "bpm" in col.lower() or "distance" in col.lower()):
                value_col = col
                break
        
        # If no value column found, use first numeric column
        if not value_col:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                value_col = numeric_cols[0]
        
        if not value_col:
            return None
        
        # Convert date column if exists
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df = df.sort_values(date_col)
                
                # Line chart for time series
                fig = px.line(df, x=date_col, y=value_col, 
                            title=f"{value_col} Over Time")
                return fig
            except:
                pass
        
        # Bar chart if no date column
        if len(df) <= 20:  # Bar chart for small datasets
            fig = px.bar(df, x=df.index, y=value_col, 
                        title=f"{value_col} Distribution")
            return fig
        else:  # Histogram for large datasets
            fig = px.histogram(df, x=value_col, 
                             title=f"{value_col} Distribution")
            return fig
    
    except Exception as e:
        print(f"Error rendering chart: {e}")
        return None

def plot_steps_timeline(data: pd.DataFrame, date_col: str, value_col: str) -> go.Figure:
    """Plot steps over time"""
    fig = px.line(data, x=date_col, y=value_col, title="Steps Over Time")
    return fig

def plot_heart_rate_distribution(data: pd.DataFrame, value_col: str) -> go.Figure:
    """Plot heart rate distribution"""
    fig = px.histogram(data, x=value_col, title="Heart Rate Distribution")
    return fig

def plot_sleep_quality(data: pd.DataFrame, date_col: str, duration_col: str) -> go.Figure:
    """Plot sleep duration over time"""
    fig = px.bar(data, x=date_col, y=duration_col, title="Sleep Duration")
    return fig

