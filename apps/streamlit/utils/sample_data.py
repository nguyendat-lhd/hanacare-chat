"""
Sample Data Generator
Creates sample health data for demo purposes when no real data is uploaded
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import os
import random

def generate_sample_data(user_id: str, storage_path: Path):
    """Generate sample health data CSV files"""
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Generate dates for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 1. Steps data
    steps_data = []
    for date in dates:
        # Convert to Python datetime if needed
        if hasattr(date, 'to_pydatetime'):
            date_obj = date.to_pydatetime()
        else:
            date_obj = date
        # Random steps between 5000-15000
        steps = np.random.randint(5000, 15000)
        steps_data.append({
            'date': date_obj.strftime('%Y-%m-%d'),
            'value': steps,
            'source': 'iPhone'
        })
    steps_df = pd.DataFrame(steps_data)
    steps_df.to_csv(storage_path / 'steps.csv', index=False)
    
    # 2. Heart Rate data (multiple readings per day)
    heart_rate_data = []
    for date in dates:
        # Convert to Python datetime if needed
        if hasattr(date, 'to_pydatetime'):
            date_obj = date.to_pydatetime()
        else:
            date_obj = date
        # 3-5 readings per day
        num_readings = np.random.randint(3, 6)
        for _ in range(num_readings):
            hour = np.random.randint(6, 22)
            minute = np.random.randint(0, 60)
            timestamp = date_obj.replace(hour=hour, minute=minute)
            # Resting HR: 60-80, Active: 80-120
            hr = np.random.randint(60, 120)
            heart_rate_data.append({
                'timestamp': timestamp.isoformat(),
                'value': hr,
                'unit': 'bpm',
                'source': 'Apple Watch'
            })
    hr_df = pd.DataFrame(heart_rate_data)
    hr_df.to_csv(storage_path / 'heart_rate.csv', index=False)
    
    # 3. Sleep data
    sleep_data = []
    for date in dates:
        # Convert to Python datetime if needed
        if hasattr(date, 'to_pydatetime'):
            date_obj = date.to_pydatetime()
        else:
            date_obj = date
        # Sleep duration: 6-9 hours
        sleep_hours = np.random.uniform(6.0, 9.0)
        sleep_start = date_obj.replace(hour=22, minute=np.random.randint(0, 60))
        sleep_end = sleep_start + timedelta(hours=sleep_hours)
        sleep_data.append({
            'date': date_obj.strftime('%Y-%m-%d'),
            'start_time': sleep_start.isoformat(),
            'end_time': sleep_end.isoformat(),
            'duration_hours': round(sleep_hours, 2),
            'quality': np.random.choice(['Good', 'Fair', 'Excellent'])
        })
    sleep_df = pd.DataFrame(sleep_data)
    sleep_df.to_csv(storage_path / 'sleep.csv', index=False)
    
    # 4. Workouts data
    workout_types = ['Running', 'Walking', 'Cycling', 'Swimming', 'Yoga']
    workouts_data = []
    # Convert dates to Python datetime list for random choice
    dates_list = [d.to_pydatetime() if hasattr(d, 'to_pydatetime') else d for d in dates]
    # Use random.sample instead of np.random.choice for list
    import random
    num_workouts = min(15, len(dates_list))
    workout_dates = random.sample(dates_list, num_workouts)
    for date_obj in workout_dates:
        workout_type = np.random.choice(workout_types)
        duration = np.random.randint(20, 90)  # minutes
        calories = np.random.randint(200, 600)
        workouts_data.append({
            'date': date_obj.strftime('%Y-%m-%d'),
            'type': workout_type,
            'duration_minutes': duration,
            'calories': calories,
            'distance_km': round(np.random.uniform(2.0, 10.0), 2) if workout_type in ['Running', 'Cycling'] else None
        })
    workouts_df = pd.DataFrame(workouts_data)
    workouts_df.to_csv(storage_path / 'workouts.csv', index=False)
    
    return {
        'steps': len(steps_data),
        'heart_rate': len(heart_rate_data),
        'sleep': len(sleep_data),
        'workouts': len(workouts_data)
    }

def ensure_sample_data(user_id: str, project_root: Path):
    """Ensure sample data exists for user"""
    storage_path = project_root / "storage" / "user_data" / user_id
    
    # Check if data already exists
    csv_files = list(storage_path.glob("*.csv")) if storage_path.exists() else []
    
    if len(csv_files) == 0:
        # Generate sample data
        return generate_sample_data(user_id, storage_path)
    else:
        return None  # Data already exists

