# main.py
import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConfigurationError

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Load .env from project root (if present)
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set. Add it to .env or environment variables (MONGO_URI=...)")

# App
app = FastAPI(title="Patient Vitals", version="1.0.0", description="Demo with web UI")

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models
class BloodPressure(BaseModel):
    systolic: Optional[int] = None
    diastolic: Optional[int] = None

class Vitals(BaseModel):
    patient_id: str
    patient_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    heart_rate: Optional[int] = None
    blood_pressure: Optional[BloodPressure] = None
    respiratory_rate: Optional[int] = None
    temperature_c: Optional[float] = None
    oxygen_saturation: Optional[int] = None
    notes: Optional[str] = None

# Reports directory
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Motor client placeholders
mongo_client: AsyncIOMotorClient | None = None
db = None

@app.on_event("startup")
async def startup_db_client():
    """
    Create Motor client, test connection, pick a DB name robustly and create helpful indexes.
    """
    global mongo_client, db
    mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    # quick connectivity test
    try:
        await mongo_client.admin.command("ping")
    except Exception as e:
        raise RuntimeError(f"Could not connect to MongoDB. Check MONGO_URI and network. ({e})")

    # Try to get default DB from URI; if missing fall back to "vitals_db"
    try:
        db = mongo_client.get_default_database()
    except ConfigurationError:
        db = mongo_client["vitals_db"]

    if db is None:
        db = mongo_client["vitals_db"]

    # log chosen DB name so you can verify in server logs
    print(f"[startup] Connected to MongoDB. Using database: {db.name}")

    # create indexes (idempotent)
    await db.vitals.create_index("patient_id")
    await db.vitals.create_index("timestamp")

@app.on_event("shutdown")
async def shutdown_db_client():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        mongo_client = None

# --- Routes ---

@app.get("/")
def index(request: Request):
    """Render the UI page (templates/index.html)."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/vitals", status_code=201)
async def post_vitals(v: Vitals):
    """Save a vitals document to MongoDB."""
    if v.timestamp is None:
        v.timestamp = datetime.utcnow()
    doc = v.dict()
    # Insert into MongoDB (Motor)
    res = await db.vitals.insert_one(doc)
    return JSONResponse({"message": "Vitals saved", "patient_id": v.patient_id, "id": str(res.inserted_id)})

@app.get("/vitals/{patient_id}")
async def get_vitals(patient_id: str):
    """Return all vitals documents for a patient (sorted newest first)."""
    cursor = db.vitals.find({"patient_id": patient_id}).sort("timestamp", -1)
    docs = []
    async for doc in cursor:
        # convert ObjectId -> str and datetime -> isoformat for JSON
        doc["_id"] = str(doc["_id"])
        ts = doc.get("timestamp")
        if isinstance(ts, datetime):
            doc["timestamp"] = ts.isoformat()
        docs.append(doc)
    if not docs:
        raise HTTPException(status_code=404, detail="No vitals for that patient")
    return docs

# PDF generator (blocking work)
def build_vitals_pdf(patient_id: str, vitals: Vitals) -> str:
    ts = vitals.timestamp.strftime("%Y%m%d%H%M%S") if vitals.timestamp else datetime.utcnow().strftime("%Y%m%d%H%M%S")
    fname = f"{patient_id}_{ts}.pdf"
    path = os.path.join(REPORTS_DIR, fname)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    left = 50
    top = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, top, f"Vitals Report - {vitals.patient_name or patient_id}")
    c.setFont("Helvetica", 11)
    c.drawString(left, top - 30, f"Patient ID: {patient_id}")
    c.drawString(left, top - 50, f"Timestamp: {vitals.timestamp.isoformat() if vitals.timestamp else 'N/A'}")

    y = top - 90
    def draw_row(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(left + 160, y, str(value))
        y -= 20

    draw_row("Heart Rate (bpm)", vitals.heart_rate or "N/A")
    bp_str = "N/A"
    if vitals.blood_pressure:
        bp_str = f"{vitals.blood_pressure.systolic}/{vitals.blood_pressure.diastolic} mmHg"
    draw_row("Blood Pressure", bp_str)
    draw_row("Respiratory Rate (breaths/min)", vitals.respiratory_rate or "N/A")
    draw_row("Temperature (°C)", vitals.temperature_c or "N/A")
    draw_row("Oxygen Saturation (%)", vitals.oxygen_saturation or "N/A")
    draw_row("Notes", vitals.notes or "-")

    c.showPage()
    c.save()
    return path

@app.get("/vitals/{patient_id}/pdf")
async def get_vitals_pdf(patient_id: str):
    """
    Fetch last vitals for the patient from MongoDB, convert to Vitals model,
    generate PDF in a background thread to avoid blocking the event loop, and return it.
    """
    # find the most recent document
    doc = await db.vitals.find_one({"patient_id": patient_id}, sort=[("timestamp", -1)])
    if not doc:
        raise HTTPException(status_code=404, detail="No vitals to make PDF")

    # normalize doc for Pydantic:
    doc.pop("_id", None)
    ts = doc.get("timestamp")
    if isinstance(ts, str):
        try:
            doc["timestamp"] = datetime.fromisoformat(ts)
        except Exception:
            doc["timestamp"] = datetime.utcnow()

    # If timestamp is a bson datetime, Motor returns a python datetime already
    v = Vitals(**doc)

    # build the PDF off the event loop
    pdf_path = await asyncio.to_thread(build_vitals_pdf, patient_id, v)
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
