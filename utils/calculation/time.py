from datetime import timedelta, datetime

def calculate_start_time(timeframe, data_points_back):
    end_time = datetime.now()
    if 'y' in timeframe:
        start_time = end_time - timedelta(days=data_points_back*365)
        return start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif 'd' in timeframe:
        start_time = end_time - timedelta(days=data_points_back)
        return start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif 'h' in timeframe:
        return end_time - timedelta(hours=data_points_back)
    elif 'm' in timeframe:
        return end_time - timedelta(minutes=data_points_back)
    
