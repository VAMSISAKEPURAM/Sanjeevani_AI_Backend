# app/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
import json

from app.db import get_db_connection
from app.utils import allowed_file, save_upload, ensure_upload_folder
from app.config import settings
from app.ml_integration import predict_image_for_crop, predict_crop_type, normalize_crop_name
from app.weather_service import capture_weather_on_login
from app.spray_prediction import run_spray_prediction

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float
    session_id: str

router = APIRouter()

@router.post("/weather/capture-login")
def trigger_weather_capture(data: WeatherRequest):
    try:
        capture_weather_on_login(data.latitude, data.longitude, data.session_id)
        # Also run spray prediction pipeline immediately after weather capture
        run_spray_prediction()
        return {"success": True, "message": "Weather data captured and processed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-image")
async def upload_image(image: UploadFile = File(...)):
    if not image or image.filename == "":
        raise HTTPException(status_code=400, detail="No file selected")
    if not allowed_file(image.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    ensure_upload_folder()
    ext = image.filename.rsplit(".", 1)[-1]
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(settings.UPLOAD_FOLDER, unique_name)

    try:
        save_upload(image, save_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()
    cursor.execute(
        "INSERT INTO plant_diagnosis (username, image_path, created_at, disease_name) VALUES (%s, %s, %s, %s)",
        ("test_user", save_path, now, "Pending")
    )
    conn.commit()
    diagnosis_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return {"success": True, "diagnosis_id": diagnosis_id, "file_path": save_path, "message": "Uploaded"}

@router.post("/predict/{crop}")
async def predict_crop(crop: str, diagnosis_id: int = Form(None), image: UploadFile = File(None)):
    image_path = None
    created_new_row = False

    if diagnosis_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM plant_diagnosis WHERE id = %s", (diagnosis_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row: raise HTTPException(status_code=404, detail="Diagnosis ID not found")
        image_path = row[0]
    else:
        if not image: raise HTTPException(status_code=400, detail="Image required")
        ensure_upload_folder()
        ext = image.filename.rsplit(".", 1)[-1]
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        image_path = os.path.join(settings.UPLOAD_FOLDER, unique_name)
        save_upload(image, image_path)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow()
        cursor.execute(
            "INSERT INTO plant_diagnosis (username, image_path, created_at, disease_name) VALUES (%s, %s, %s, %s)",
            ("test_user", image_path, now, "Pending")
        )
        conn.commit()
        diagnosis_id = cursor.lastrowid
        cursor.close()
        conn.close()
        created_new_row = True

    try:
        verification = predict_crop_type(image_path)
        detected_crop = verification["label"]
        detected_conf = verification["confidence"]
        norm_selected = normalize_crop_name(crop)
        norm_detected = normalize_crop_name(detected_crop)
        
        if norm_selected != norm_detected:
            return {
                "success": False, "match": False,
                "detail": f"Mismatch: Selected {crop}, Detected {detected_crop} ({detected_conf:.2f})",
                "detected": detected_crop, "confidence": detected_conf
            }
    except Exception as e:
        print(f"Verification warning: {e}")

    try:
        result = predict_image_for_crop(image_path, crop)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    predicted_label = result["label"]
    confidence = result["confidence"]
    
    if confidence < 0.60:
        return {
            "success": False, "match": False,
            "detail": f"Low confidence ({confidence:.2f}). Please upload a better image.",
            "detected": predicted_label, "confidence": confidence
        }

    # Fetch pesticide info from DB, fallback to code-dict
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Check if table exists (optional, assuming it stands)
    try:
        cursor.execute("SELECT * FROM pesticide_recommendation WHERE disease = %s", (predicted_label,))
        pesticide_info = cursor.fetchone()
    except Exception:
        pesticide_info = None
    
    # If not found in DB, return empty or default structure
    if not pesticide_info:
        pesticide_info = {
            "disease": predicted_label,
            "chemical_pesticides": "Consult local expert",
            "cause_prevention": "Ensure good field hygiene"
        }

    extra_json = json.dumps({
        "probabilities": result.get("probabilities", []),
        "treatment": pesticide_info,
        "model_used": result.get("model_file")
    })
    
    cursor.execute(
        "UPDATE plant_diagnosis SET disease_name = %s, confidence = %s, extra_json = %s, updated_at = %s WHERE id = %s",
        (predicted_label, confidence, extra_json, datetime.utcnow(), diagnosis_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "success": True, "diagnosis_id": diagnosis_id,
        "predicted_label": predicted_label, "confidence": confidence,
        "treatment_info": pesticide_info, "created_new_row": created_new_row
    }

@router.get("/diagnosis/{diagnosis_id}")
def get_diagnosis(diagnosis_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM plant_diagnosis WHERE id = %s", (diagnosis_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row: raise HTTPException(status_code=404, detail="Not found")
    if row.get("image_path"): row["image_path"] = row["image_path"].replace("\\", "/")
    return {"success": True, "diagnosis": row}

@router.get("/spray/best-time")
def get_best_spray_time():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT created_at FROM Weather_data ORDER BY id DESC LIMIT 1")
        last_row = cursor.fetchone()
        if not last_row: return {"success": True, "data": []}
        
        session_time = last_row['created_at']
        cursor.execute("""
            SELECT temperature_c, humidity_percent, rainfall_mm, forecast_date, status 
            FROM Spray_time_prediction 
            WHERE created_at = %s AND (status = '1' OR status = '1.0')
            ORDER BY forecast_date ASC
        """, (session_time,))
        records = cursor.fetchall()
        
        # Grouping logic
        from collections import defaultdict
        grouped = defaultdict(list)
        for r in records:
            if not r['forecast_date']: continue
            hour = r['forecast_date'].hour
            if 4 <= hour < 22:
                grouped[r['forecast_date'].date()].append(r)
        
        results = []
        for day in sorted(grouped.keys()):
            results.extend(grouped[day][:2])
            
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
