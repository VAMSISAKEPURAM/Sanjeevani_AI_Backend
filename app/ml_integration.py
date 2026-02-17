# app/ml_integration.py
import os
import numpy as np
from PIL import Image
from typing import Dict, Any
from huggingface_hub import hf_hub_download
import tensorflow as tf
import pickle
from tensorflow.keras.applications.efficientnet import preprocess_input as eff_preprocess_input

# === CONFIGURATION ===
MODEL_CONFIG = {
    "chilli": {
        "filename": "Chilli_EfficientNetB4_best.keras",
        "img_size": 300,
        "classes": ['Chill_healthy', 'Chilli __Whitefly', 'Chilli __Yellowish', 'Chilli__Anthracnos', 'Chilli__Damping_Off', 'Chilli__Leaf_Curl_Virus', 'Chilli__Leaf_Spot']
    },
    "corn": {
        "filename": "Corn_EfficientNetB4_best.keras",
        "img_size": 300,
        "classes": ['Common Rust', 'Corn_Blight', 'Gray Leaf Spot', 'Healthy', 'Northern Leaf Blight']
    },
    "groundnut": {
        "filename": "GroundNut_EfficientNetB0_best.keras",
        "img_size": 224,
        "classes": ['Ground_Nut_early_leaf_spot_1', 'Ground_Nut_early_rust_1', 'Ground_Nut_healthy_leaf_1', 'Ground_Nut_late_leaf_spot_1', 'Ground_Nut_nutrition_deficiency_1', 'Ground_Nut_rust_1']
    },
    "paddy": {
        "filename": "Paddy_EfficientNetB0_best.keras",
        "img_size": 224,
        "classes": ['Paddy_BLAST', 'Paddy_BLIGHT', 'Paddy_BROWNSPOT', 'Paddy_HEALTHY']
    },
    "sugarcane": {
        "filename": "Sugarcane_EfficientNetB4_best.keras",
        "img_size": 224,
        "classes": ['BacterialBlights', 'Healthy', 'Mosaic', 'RedRot', 'Rust', 'Yellow']
    },
    "tomato": {
        "filename": "Tomato_EfficientNetB4_best.keras",
        "img_size": 300,
        "classes": ['Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy']
    }
}

BASE_MODEL_FILENAME = "Crop_Classifier_EfficientNetB4_best.keras"
SPRAY_MODEL_FILENAME = "weather_spray_model.pkl"

BASE_CLASSES = ['Chilli', 'Corn', 'Groundnut', 'Paddy', 'Sugarcane', 'Tomato']
CANONICAL_CROPS = {"chilli", "corn", "groundnut", "paddy", "tomato", "sugarcane"}

# === CACHE ===
LOADED_MODELS = {}
BASE_MODEL = None
SPRAY_MODEL = None

# === HUGGING FACE LOADER ===
def load_model_from_hf(filename):
    print(f"Loading model {filename} from Hugging Face...")
    try:
        model_path = hf_hub_download(
            repo_id="Vamsi232/Sanjeevani",
            filename=filename
        )
        if filename.endswith(".pkl"):
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        else:
            return tf.keras.models.load_model(model_path)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load model {filename}: {e}")
        raise e

# === LAZY LOADERS ===
def get_model(crop_key):
    global LOADED_MODELS
    if crop_key not in MODEL_CONFIG:
        raise ValueError(f"Unknown crop '{crop_key}'")
    
    if crop_key not in LOADED_MODELS:
        filename = MODEL_CONFIG[crop_key]["filename"]
        LOADED_MODELS[crop_key] = load_model_from_hf(filename)
    
    return LOADED_MODELS[crop_key]

def get_base_model():
    global BASE_MODEL
    if BASE_MODEL is None:
        BASE_MODEL = load_model_from_hf(BASE_MODEL_FILENAME)
    return BASE_MODEL

def get_spray_model():
    global SPRAY_MODEL
    if SPRAY_MODEL is None:
        SPRAY_MODEL = load_model_from_hf(SPRAY_MODEL_FILENAME)
    return SPRAY_MODEL

def _preprocess_image(image_path: str, target_size: int) -> np.ndarray:
    """
    Preprocess the input image:
      - Open image (RGB), resize to target_size x target_size
      - Convert to float32 and apply EfficientNet preprocess_input
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize((target_size, target_size))
    arr = np.asarray(img).astype("float32")
    arr = eff_preprocess_input(arr)
    return np.expand_dims(arr, axis=0)

def normalize_crop_name(name: str) -> str:
    if not name: return ""
    clean = name.lower().strip()
    clean_nospace = clean.replace(" ", "").replace("_", "")
    
    if "chilli" in clean_nospace or "chili" in clean_nospace: return "chilli"
    if "corn" in clean_nospace or "maize" in clean_nospace: return "corn"
    if "ground" in clean_nospace and "nut" in clean_nospace: return "groundnut"
    if "paddy" in clean_nospace or "rice" in clean_nospace: return "paddy"
    if "sugar" in clean_nospace and "cane" in clean_nospace: return "sugarcane"
    if "tomato" in clean_nospace or "tomoto" in clean_nospace: return "tomato"
    
    return clean_nospace

def predict_image_for_crop(image_path: str, crop_key: str) -> Dict[str, Any]:
    crop_key = normalize_crop_name(crop_key)
    if crop_key not in MODEL_CONFIG:
        raise ValueError(f"Unknown crop '{crop_key}'. Choose one of: {list(MODEL_CONFIG.keys())}")

    model = get_model(crop_key)
    img_size = MODEL_CONFIG[crop_key]["img_size"]
    classes = MODEL_CONFIG[crop_key]["classes"]

    x = _preprocess_image(image_path, img_size)
    preds = model.predict(x)
    
    # Handle output shape
    if isinstance(preds, list): preds = preds[0]
    probs = np.asarray(preds).reshape(-1)

    # Softmax check
    if not np.isclose(probs.sum(), 1.0):
        exp = np.exp(probs - np.max(probs))
        probs = exp / exp.sum()

    top_index = int(np.argmax(probs))
    top_label = classes[top_index] if top_index < len(classes) else str(top_index)
    confidence = float(probs[top_index])

    return {
        "label": top_label,
        "index": top_index,
        "confidence": confidence,
        "probabilities": probs.tolist(),
        "model_file": "HF_Hub_Model",
        "crop": crop_key
    }

def predict_crop_type(image_path: str) -> Dict[str, Any]:
    # Base classifier uses 224
    img_size = 224
    
    model = get_base_model()
    x = _preprocess_image(image_path, img_size)
    preds = model.predict(x)
    probs = np.asarray(preds).flatten()
    
    if not np.isclose(probs.sum(), 1.0):
        exp = np.exp(probs - np.max(probs))
        probs = exp / exp.sum()
        
    top_index = int(np.argmax(probs))
    
    if top_index < len(BASE_CLASSES):
        top_label = BASE_CLASSES[top_index]
    else:
        top_label = f"Unknown_Class_{top_index}"
        
    confidence = float(probs[top_index])
    
    return {
        "label": top_label,
        "confidence": confidence,
        "probabilities": probs.tolist()
    }
