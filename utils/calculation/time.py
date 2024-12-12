from datetime import timedelta, datetime

def calculate_start_time(timeframe, data_points_back):
    end_time = datetime.now()
    if 'y' in timeframe:
        start_time = end_time - timedelta(days=data_points_back*365)
        return start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif 'd' in timeframe:
        prefix = int(timeframe.split('d')[0])
        start_time = end_time - timedelta(days=data_points_back)
        return start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif 'h' in timeframe:
        prefix = int(timeframe.split('h')[0])
        return end_time - timedelta(hours=prefix*data_points_back)
    elif 'm' in timeframe:
        prefix = int(timeframe.split('m')[0])
        return end_time - timedelta(minutes=prefix*data_points_back)
    
