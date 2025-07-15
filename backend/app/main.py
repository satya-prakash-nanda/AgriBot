# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
from dotenv import load_dotenv
from app.api.routes import create_router
from app.core.logger import setup_logger
import os  # ✅ NEW

# ✅ Load .env variables
load_dotenv()

# ✅ Initialize FastAPI
app = FastAPI(title="Agribot_new Backend")

# ✅ Setup logging
setup_logger()

# ✅ Serve static files (e.g. speech audio)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # This points to /backend
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register your routes
app.include_router(create_router())

# ✅ Basic health check route
@app.get("/")
async def root():
    return {"message": "Agribot_new backend is running!"}
