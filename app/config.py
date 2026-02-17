import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database config is primarily handled via DATABASE_URL in db.py
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./static/uploads")
    MODEL_FOLDER = os.getenv("MODEL_FOLDER", "./models")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "0e353b69178bef3dcaa9a2349e7ef65a")

settings = Settings()
