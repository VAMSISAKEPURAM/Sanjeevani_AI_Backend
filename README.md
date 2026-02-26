<div align="center">
  <img src="https://via.placeholder.com/150?text=Sanjeevani+AI+Backend" alt="Project Logo" width="120" height="120" style="border-radius: 20px;">
  
  # 🚀 Sanjeevani AI Backend

  <p align="center">
    <strong>A high-performance, ML-powered backend engine serving AI inferences and data.</strong>
  </p>
  
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#architecture-overview">Architecture</a> •
    <a href="#environment-variables">Environment Variables</a> •
    <a href="#installation--local-setup">Installation</a>
  </p>

  <p align="center">
    <!-- Shields for the actual tech stack -->
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
    <img src="https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" alt="TensorFlow" />
    <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="Scikit-Learn" />
  </p>
</div>

---

## 📖 Overview

**Sanjeevani AI Backend** is the core ML and data processing engine that powers the front-facing application. Built completely on **FastAPI**, it is engineered to serve synchronous REST API connections, handle heavy deep-learning model inferences, scale data analytics, and interface securely with our database infrastructure.

---

## 💻 Tech Stack

| Category | Technology |
|---|---|
| **Core Framework** | Python & FastAPI |
| **Server Engine** | Uvicorn |
| **Database Gateway** | MySQL Connector (`mysql-connector-python`) |
| **Deep Learning** | TensorFlow 2.x |
| **Machine Learning** | Scikit-Learn, Pandas, Numpy, Joblib |
| **Computer Vision** | OpenCV Headless, Pillow |

---

## 🏗 Architecture Overview

This backend is architected to isolate core concerns like routing, ML inference, and database schemas:
- **FastAPI Core:** Leverages Python type-hints to automatically validate inputs and generate interactive Swagger/ReDoc documentations.
- **ML Services Layer:** Decoupled AI predictions where models (`.keras` and `.pkl`) are pre-loaded entirely into memory at startup to remove latency.
- **RESTful Endpoints:** Fully modular routing system implemented under `app.routes`.
- **CORS Configuration:** Protected middleware that strictly enforces accepted cross-origin policies for our frontend domain.

---

## ✨ Key Features

- **⚡ Asynchronous IO:** Native async handlers provide ultra-low latency response times for concurrently heavy workloads.
- **🧠 Deep Learning Inferences:** Serves robust `.keras` Convolutional Neural Networks (CNN) for image analysis.
- **📊 Predictive Machine Learning:** Operates Scikit-Learn `.pkl` predictive models alongside automated mathematical scaling.
- **🗄️ Relational Data Storage:** Complete state synchronization acting closely with MySQL native databases.
- **📝 Automated OpenAPI:** Auto-generated endpoints Swagger documentation available out-of-the-box (`/docs`).

---

## 📂 Folder Structure

```text
📦 sanjeevani-backend/
 ┣ 📂 app/                 # Main application directory
 ┃ ┣ 📜 routes.py          # API Routers and application endpoints
 ┃ ┗ 📜 utils.py           # Core utilities and data formatting tools
 ┣ 📂 models/              # Serialized AI models (Git-Ignored conceptually)
 ┃ ┣ 📜 my_cnn_model_New.keras      # Serialized TensorFlow Model
 ┃ ┣ 📜 weather_prediction_model.pkl# Pre-trained ML Scikit Model
 ┃ ┣ 📜 ml_feature_names.json       # Feature matrix mapping
 ┃ ┗ 📜 ml_scaler.pkl               # ML Model Scaling parameters
 ┣ 📂 static/              # Storage (e.g., uploads)
 ┣ 📜 check_*.py           # Verification and helper scripts 
 ┣ 📜 main.py              # Application entry point/FastAPI setup
 ┣ 📜 .env                 # Environment config file
 ┗ 📜 requirements.txt     # Python dependencies mapping
```

---

## 🔐 Environment Variables

Create a `.env` file directly residing in the root folder using these configuration setups:

```env
# Database Credentials
DB_HOST=localhost
DB_USER=root
DB_PASS=your_password
DB_NAME=sanjeevaniai2
DB_AUTH_PLUGIN=mysql_native_password

# External Integrations
OPENWEATHER_API_KEY=your_openweather_api_key

# ML Model Paths
MODEL_PATH=./models/my_cnn_model_New.keras
ML_MODEL_PATH=./models/weather_prediction_model.pkl
FEATURES_JSON_PATH=./models/ml_feature_names.json
SCALER_PATH=./models/ml_scaler.pkl

# Internal System Limits
UPLOAD_FOLDER=./static/uploads
MAX_CONTENT_LENGTH=5242880
ALLOWED_EXT=png,jpg,jpeg,gif
```

*(Important: Never commit sensitive properties, databases, or API keys directly to your Git repository.)*

---

## 🚀 Installation & Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/<your-username>/sanjeevani-ai.git
```

**2. Navigate to the backend workspace**
```bash
cd sanjeevani-ai/sanjeevani-backend
```

**3. Setup Python Virtual Environment (Recommended)**
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On MacOS/Linux:
source .venv/bin/activate
```

**4. Install Dependencies**
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the Project

Start up the API server using Uvicorn:

```bash
uvicorn main:app --reload
```

The server will automatically bind and listen locally. 
- You can access the API directly: `http://localhost:8000`
- You can explore the Interactive Documentation (Swagger UI): `http://localhost:8000/docs`

---

## ☁️ Deployment Guide

This project is primed to be seamlessly deployed into services such as **Railway, Render, AWS, or DigitalOcean**.

**PaaS Deployment (e.g., Railway/Render):**
1. Connect this repository to your respective platform.
2. Root directory: Ensure the build targets `sanjeevani-backend` properly.
3. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set up the exact Environment Variables inside your deployment dashboard.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
<p align="center"><i>Crafted with logic and extreme performance architectures.</i></p>
