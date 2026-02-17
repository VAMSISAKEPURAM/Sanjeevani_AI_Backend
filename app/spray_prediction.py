# app/spray_prediction.py
import mysql.connector
import numpy as np
from app.db import get_db_connection
from app.ml_integration import get_spray_model

def create_prediction_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    table_query = """
    CREATE TABLE IF NOT EXISTS Spray_time_prediction (
        id INT AUTO_INCREMENT PRIMARY KEY,
        temperature_c FLOAT NOT NULL,
        humidity_percent FLOAT NOT NULL,
        rainfall_mm FLOAT NOT NULL,
        created_at DATETIME NOT NULL,
        forecast_date DATETIME NULL,
        status VARCHAR(255) NOT NULL,
        unique_column VARCHAR(255),
        INDEX(created_at)
    );
    """
    try:
        cursor.execute(table_query)
        conn.commit()
        print("Spray_time_prediction table ensured.")
    except Exception as e:
        print(f"Error creating prediction table: {e}")
    finally:
        cursor.close()
        conn.close()

def fetch_latest_session_records():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Weather_data ORDER BY id DESC LIMIT 1")
        last = cursor.fetchone()
        if not last: return []
        
        session_time = last['created_at']
        cursor.execute("SELECT * FROM Weather_data WHERE created_at = %s", (session_time,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching records: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def generate_predictions(records):
    predictions = []
    if not records: return []
    
    for row in records:
        try:
            features = [[
                row['temperature_c'],
                row['humidity_percent'],
                row['rainfall_mm']
            ]]
            pred = get_spray_model().predict(features)
            status = pred[0]
            predictions.append({"original_row": row, "status": status})
        except Exception as e:
            print(f"Error predicting for row {row.get('id')}: {e}")
    return predictions

def store_prediction_records(predictions):
    if not predictions: return
    conn = get_db_connection()
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO Spray_time_prediction 
    (temperature_c, humidity_percent, rainfall_mm, created_at, forecast_date, status, unique_column)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    data = []
    for p in predictions:
        row = p['original_row']
        data.append((
            row['temperature_c'], row['humidity_percent'], row['rainfall_mm'],
            row['created_at'], row['forecast_date'], str(p['status']), row['unique_column']
        ))
    try:
        cursor.executemany(insert_query, data)
        conn.commit()
    except Exception as e:
        print(f"Error inserting predictions: {e}")
    finally:
        cursor.close()
        conn.close()

def run_spray_prediction():
    print("Starting Spray Prediction...")
    create_prediction_table()
    records = fetch_latest_session_records()
    if records:
        preds = generate_predictions(records)
        store_prediction_records(preds)
    print("Pipeline completed.")

if __name__ == "__main__":
    run_spray_prediction()
