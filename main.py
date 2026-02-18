import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI()

# -----------------------------
# CORS Configuration
# -----------------------------
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "https://sanjeevani-ai-frontend.vercel.app"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Include Routes
# -----------------------------
app.include_router(router)

# -----------------------------
# Health Check (VERY IMPORTANT)
# -----------------------------
@app.get("/")
def health_check():
    return {"status": "Backend running successfully"}
