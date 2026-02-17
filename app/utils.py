import os
from fastapi import UploadFile
from app.config import settings
from PIL import Image, UnidentifiedImageError

def ensure_upload_folder():
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg"}

def save_upload(file: UploadFile, dest_path: str):
    """
    Save incoming UploadFile to dest_path. Also perform a lightweight image sanity check.
    """
    # Make sure parent directory exists
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Write file
    with open(dest_path, "wb") as f:
        f.write(file.file.read())

    # Basic validation: try to open with Pillow
    try:
        with Image.open(dest_path) as img:
            img.verify()  # will raise if not valid image
    except (UnidentifiedImageError, Exception):
        # remove invalid file
        try:
            os.remove(dest_path)
        except Exception:
            pass
        raise

    return dest_path
