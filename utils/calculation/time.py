from datetime import timedelta, datetime

def calculate_start_time(timeframe, data_points_back):
    end_time = datetime.now()
    if 'y' in timeframe:
        return end_time - timedelta(days=data_points_back*365)
    elif 'd' in timeframe:
        return end_time - timedelta(days=data_points_back)
    elif 'h' in timeframe:
        return end_time - timedelta(hours=data_points_back)
    elif 'm' in timeframe:
        return end_time - timedelta(minutes=data_points_back)
    