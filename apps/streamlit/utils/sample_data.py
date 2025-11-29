"""
Sample Data Generator
Creates sample health data for demo purposes when no real data is uploaded
Generates realistic health data in Apple Health export format
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import os
import random

def generate_sample_data(user_id: str, storage_path: Path):
    """Generate sample health data CSV files with realistic data"""
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Generate dates for last 90 days (more data for better queries)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates_list = [d.to_pydatetime() if hasattr(d, 'to_pydatetime') else d for d in dates]
    
    # 1. Steps data (Apple Health format: startDate, endDate, value, unit, sourceName)
    steps_data = []
    for date in dates_list:
        # Weekend has more steps
        is_weekend = date.weekday() >= 5
        base_steps = np.random.randint(8000, 12000) if is_weekend else np.random.randint(5000, 10000)
        
        # Create hourly steps distribution (more steps during day)
        for hour in range(6, 23):
            if hour in [6, 7, 8, 9, 17, 18, 19, 20]:  # Morning and evening peaks
                hour_steps = np.random.randint(500, 1500)
            elif hour in [10, 11, 12, 13, 14, 15, 16]:  # Daytime
                hour_steps = np.random.randint(200, 800)
            else:  # Evening
                hour_steps = np.random.randint(100, 500)
            
            start_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            steps_data.append({
                'startDate': start_time.strftime('%Y-%m-%d %H:%M:%S +0000'),
                'endDate': end_time.strftime('%Y-%m-%d %H:%M:%S +0000'),
                'value': hour_steps,
                'unit': 'count',
                'sourceName': 'iPhone'
            })
    
    steps_df = pd.DataFrame(steps_data)
    steps_df.to_csv(storage_path / 'steps.csv', index=False)
    
    # 2. Heart Rate data (multiple readings per day, Apple Health format)
    heart_rate_data = []
    for date in dates_list:
        # More readings during active hours
        num_readings = np.random.randint(8, 15)  # More readings per day
        
        for _ in range(num_readings):
            hour = np.random.randint(6, 23)
            minute = np.random.randint(0, 60)
            second = np.random.randint(0, 60)
            start_time = date.replace(hour=hour, minute=minute, second=second, microsecond=0)
            end_time = start_time + timedelta(minutes=1)
            
            # Heart rate varies by time of day and activity
            if hour in [6, 7, 8, 22, 23]:  # Morning/evening (resting)
                hr = np.random.randint(55, 75)
            elif hour in [9, 10, 11, 12, 13, 14, 15, 16, 17]:  # Daytime (normal)
                hr = np.random.randint(65, 85)
            else:  # Evening (slightly elevated)
                hr = np.random.randint(70, 90)
            
            heart_rate_data.append({
                'startDate': start_time.strftime('%Y-%m-%d %H:%M:%S +0000'),
                'endDate': end_time.strftime('%Y-%m-%d %H:%M:%S +0000'),
                'value': hr,
                'unit': 'count/min',
                'sourceName': 'Apple Watch'
            })
    
    hr_df = pd.DataFrame(heart_rate_data)
    hr_df.to_csv(storage_path / 'heart_rate.csv', index=False)
    
    # 3. Sleep data (Apple Health format)
    # Ensure we have data in the last 7 days (most recent dates first)
    sleep_data = []
    # Sort dates to process most recent first, ensuring recent data exists
    sorted_dates = sorted(dates_list, reverse=True)
    
    for i, date in enumerate(sorted_dates):
        # Sleep pattern: go to bed between 22:00-23:30, wake up 6:00-8:00
        bed_hour = np.random.randint(22, 24)
        bed_minute = np.random.randint(0, 30) if bed_hour == 22 else np.random.randint(0, 30)
        sleep_start = date.replace(hour=bed_hour, minute=bed_minute, second=0, microsecond=0)
        
        # Sleep duration: 6.5-8.5 hours
        sleep_hours = np.random.uniform(6.5, 8.5)
        sleep_end = sleep_start + timedelta(hours=sleep_hours)
        
        # If sleep ends next day, adjust
        if sleep_end.day != sleep_start.day or sleep_end < sleep_start:
            next_day = date + timedelta(days=1)
            sleep_end = next_day.replace(
                hour=np.random.randint(6, 8),
                minute=np.random.randint(0, 60),
                second=0,
                microsecond=0
            )
        
        # Ensure endDate is after startDate
        if sleep_end <= sleep_start:
            sleep_end = sleep_start + timedelta(hours=7)
        
        sleep_data.append({
            'startDate': sleep_start.strftime('%Y-%m-%d %H:%M:%S +0000'),
            'endDate': sleep_end.strftime('%Y-%m-%d %H:%M:%S +0000'),
            'value': round(sleep_hours, 2),
            'unit': 'hr',
            'sourceName': 'Apple Watch'
        })
    
    sleep_df = pd.DataFrame(sleep_data)
    sleep_df.to_csv(storage_path / 'sleep.csv', index=False)
    
    # 4. Workouts data (Apple Health format)
    workout_types = ['Running', 'Walking', 'Cycling', 'Swimming', 'Yoga', 'Strength Training']
    workouts_data = []
    
    # Generate workouts: 2-4 per week
    num_workouts = np.random.randint(18, 36)  # ~2-4 per week over 90 days
    workout_dates = random.sample(dates_list, min(num_workouts, len(dates_list)))
    
    for date_obj in workout_dates:
        workout_type = np.random.choice(workout_types)
        
        # Workout time: morning (6-9), afternoon (12-15), or evening (17-20)
        time_slot = np.random.choice(['morning', 'afternoon', 'evening'], p=[0.3, 0.2, 0.5])
        if time_slot == 'morning':
            start_hour = np.random.randint(6, 9)
        elif time_slot == 'afternoon':
            start_hour = np.random.randint(12, 15)
        else:
            start_hour = np.random.randint(17, 20)
        
        start_minute = np.random.randint(0, 60)
        workout_start = date_obj.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        # Duration based on workout type
        if workout_type == 'Running':
            duration_minutes = np.random.randint(20, 60)
            calories = np.random.randint(300, 700)
            distance = round(np.random.uniform(3.0, 10.0), 2)
        elif workout_type == 'Walking':
            duration_minutes = np.random.randint(30, 90)
            calories = np.random.randint(150, 400)
            distance = round(np.random.uniform(2.0, 6.0), 2)
        elif workout_type == 'Cycling':
            duration_minutes = np.random.randint(30, 90)
            calories = np.random.randint(400, 800)
            distance = round(np.random.uniform(10.0, 30.0), 2)
        elif workout_type == 'Swimming':
            duration_minutes = np.random.randint(30, 60)
            calories = np.random.randint(300, 600)
            distance = None
        elif workout_type == 'Yoga':
            duration_minutes = np.random.randint(30, 60)
            calories = np.random.randint(100, 250)
            distance = None
        else:  # Strength Training
            duration_minutes = np.random.randint(45, 90)
            calories = np.random.randint(200, 500)
            distance = None
        
        workout_end = workout_start + timedelta(minutes=duration_minutes)
        
        workout_record = {
            'startDate': workout_start.strftime('%Y-%m-%d %H:%M:%S +0000'),
            'endDate': workout_end.strftime('%Y-%m-%d %H:%M:%S +0000'),
            'value': duration_minutes,
            'unit': 'min',
            'workoutType': workout_type,
            'totalEnergyBurned': calories,
            'totalDistance': distance,
            'sourceName': 'Apple Watch'
        }
        workouts_data.append(workout_record)
    
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

