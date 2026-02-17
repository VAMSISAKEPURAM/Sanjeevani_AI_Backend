
import mysql.connector
import requests
import datetime
from collections import defaultdict
from app.db import get_db_connection
from app.config import settings

def init_weather_table():
    """Create the Weather_data table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    table_schema = """
    CREATE TABLE IF NOT EXISTS Weather_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        temperature_c FLOAT NOT NULL,
        humidity_percent FLOAT NOT NULL,
        rainfall_mm FLOAT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        forecast_date DATETIME NULL,
        latitude DOUBLE NULL,
        longitude DOUBLE NULL,
        source VARCHAR(255) NULL,
        unique_column VARCHAR(255) UNIQUE
    );
    """
    try:
        cursor.execute(table_schema)
        conn.commit()
        print("Weather_data table ensured to exist.")
    except Exception as e:
        print(f"Error creating/checking table: {e}")
    finally:
        cursor.close()
        conn.close()

def fetch_forecast_weather(lat, lon):
    """Fetch 5-day / 3-hour forecast from OpenWeather."""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        print("Error: OPENWEATHER_API_KEY not set.")
        return None

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        return None

def process_weather_blocks(forecast_data, lat, lon):
    """Process raw forecast data into 6-hour blocks."""
    if not forecast_data or "list" not in forecast_data:
        return []

    timezone_offset = forecast_data.get("city", {}).get("timezone", 0)
    records = forecast_data["list"]
    daily_blocks = defaultdict(lambda: defaultdict(list))
    
    def get_block_info(local_dt):
        hour = local_dt.hour
        if 4 <= hour < 10: return True, 1, 0
        elif 10 <= hour < 16: return True, 2, 0
        elif 16 <= hour < 22: return True, 3, 0
        elif 22 <= hour: return True, 4, 0
        elif 0 <= hour < 2: return True, 4, -1
        return False, 0, 0

    valid_days_found = set()
    
    for item in records:
        dt_ts = item.get("dt")
        main = item.get("main", {})
        temp = main.get("temp")
        hum = main.get("humidity")
        rain = item.get("rain", {}).get("3h", 0.0)
        
        utc_dt = datetime.datetime.utcfromtimestamp(dt_ts)
        local_dt = utc_dt + datetime.timedelta(seconds=timezone_offset)
        
        is_window, block_idx, day_offset = get_block_info(local_dt)
        if is_window:
            operational_date = (local_dt + datetime.timedelta(days=day_offset)).date()
            daily_blocks[operational_date][block_idx].append({
                "temp": temp, "hum": hum, "rain": rain, "time": local_dt
            })
            valid_days_found.add(operational_date)

    sorted_days = sorted(list(valid_days_found))[:5]
    processed_records = []
    
    for day_idx, day_date in enumerate(sorted_days):
        for block_idx in range(1, 5):
            points = daily_blocks[day_date][block_idx]
            if points:
                avg_temp = sum(p["temp"] for p in points) / len(points)
                avg_hum = sum(p["hum"] for p in points) / len(points)
                total_rain = sum(p["rain"] for p in points)
                ref_time = points[0]["time"]
            else:
                avg_temp, avg_hum, total_rain = 0.0, 0.0, 0.0
                ref_time = datetime.datetime.combine(day_date, datetime.time(4 + (block_idx-1)*6, 0))
            
            processed_records.append({
                "day_index": day_idx + 1,
                "block_index": block_idx,
                "temperature_c": round(avg_temp, 2),
                "humidity_percent": round(avg_hum, 2),
                "rainfall_mm": round(total_rain, 2),
                "forecast_date": ref_time,
                "lat": lat,
                "lon": lon
            })
    return processed_records

def db_insert_weather_records(records, login_unique_key):
    """Insert processed records into Weather_data table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO Weather_data 
    (temperature_c, humidity_percent, rainfall_mm, forecast_date, latitude, longitude, source, unique_column)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        temperature_c=VALUES(temperature_c),
        humidity_percent=VALUES(humidity_percent),
        rainfall_mm=VALUES(rainfall_mm),
        source=VALUES(source)
    """
    try:
        data_to_insert = []
        for r in records:
            unique_col = f"{login_unique_key}_{r['day_index']}_{r['block_index']}"
            data_to_insert.append((
                r["temperature_c"], r["humidity_percent"], r["rainfall_mm"],
                r["forecast_date"], r["lat"], r["lon"], "OpenWeatherMap", unique_col
            ))
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
    except Exception as err:
        print(f"Error inserting weather records: {err}")
    finally:
        cursor.close()
        conn.close()

def capture_weather_on_login(lat, lon, login_unique_key):
    print(f"Starting weather capture for {lat}, {lon} | Session: {login_unique_key}")
    init_weather_table()
    forecast = fetch_forecast_weather(lat, lon)
    if forecast:
        processed_records = process_weather_blocks(forecast, lat, lon)
        if processed_records:
            db_insert_weather_records(processed_records, login_unique_key)


