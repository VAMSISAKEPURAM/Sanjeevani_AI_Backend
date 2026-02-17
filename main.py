import os
from fastapi import FastAPI
import uvicorn
from app.routes import router

app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
