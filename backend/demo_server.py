"""
Lightweight demo server — SQLite, geen PostGIS/pgvector nodig.
Start met: python3 demo_server.py
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import uuid, json

app = FastAPI(title="InfraRaming Demo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory store ---
projects = {}
risks = {}
permits = {}
estimations = {}

# --- Seed data ---
seed_id = "demo-project-001"
projects[seed_id] = {
    "id": seed_id,
    "project_number": "2024-GAS-0042",
    "name": "Aardgasleiding Nieuw-West Amsterdam",
    "client": "Liander N.V.",
    "location": "Amsterdam Nieuw-West",
    "phase": "DO",
    "discipline": "Gas",
    "status": "actief",
    "start_date": "2024-03-01",
    "end_date": "2024-11-30",
    "scope_description": "Vervanging 2.4 km middendruk aardgasleiding DN200 in woonwijk. Inclusief 48 aansluitingen, 3 kruisingen met hoofdwegen en 1 spoorwegkruising.",
    "budget_estimated": 1850000,
    "budget_actual": 1240000,
    "hours_estimated": 4200,
    "hours_actual": 2890,
    "organization_id": "org-liander",
    "created_at": "2024-01-15T09:00:00",
    "updated_at": "2024-04-20T14:30:00",
}

risks[seed_id] = [
    {"id": "r1", "project_id": seed_id, "description": "Spoorwegkruising ProRail — vergunningvertraging", "category": "Vergunning", "probability": 3, "impact": 4, "score": 12, "owner": "Omgevingsmanager", "mitigation_measure": "Vroegtijdig contact ProRail, preassembly buiten railzone", "deadline": "2024-05-01", "status": "open", "auto_detected": True},
    {"id": "r2", "project_id": seed_id, "description": "Vervuilde grond (historisch tankstation)", "category": "Bodem", "probability": 2, "impact": 5, "score": 10, "owner": "Projectmanager", "mitigation_measure": "Bodemonderzoek fase 2 uitvoeren voor aanvang graafwerk", "deadline": "2024-04-15", "status": "in_behandeling", "auto_detected": True},
    {"id": "r3", "project_id": seed_id, "description": "Congestie machinepark zomer 2024", "category": "Capaciteit", "probability": 4, "impact": 3, "score": 12, "owner": "Werkvoorbereider", "mitigation_measure": "Reservering aannemers voor week 28-36 bevestigen", "deadline": "2024-03-30", "status": "open", "auto_detected": False},
    {"id": "r4", "project_id": seed_id, "description": "Archeologische toevalsvondst", "category": "Archeologie", "probability": 2, "impact": 3, "score": 6, "owner": "Omgevingsmanager", "mitigation_measure": "Archeologisch protocol opnemen in werkplan", "deadline": "2024-04-01", "status": "gesloten", "auto_detected": True},
]

permits[seed_id] = [
    {"id": "p1", "project_id": seed_id, "permit_type": "Instemmingsbesluit", "description": "Instemming netbeheerder voor werkzaamheden in openbare weg", "authority": "gemeente", "status": "verleend", "submission_date": "2024-01-20", "expected_approval": "2024-03-01", "actual_approval": "2024-02-28", "risk_level": "laag", "auto_detected": True},
    {"id": "p2", "project_id": seed_id, "permit_type": "Verkeersmaatregelen BABW", "description": "Tijdelijke verkeersmaatregelen voor graafwerkzaamheden A'dam Nieuw-West", "authority": "gemeente", "status": "in_behandeling", "submission_date": "2024-03-15", "expected_approval": "2024-05-10", "actual_approval": None, "risk_level": "middel", "auto_detected": True},
    {"id": "p3", "project_id": seed_id, "permit_type": "Spoorvergunning ProRail", "description": "Toestemming werkzaamheden nabij spoorzone Lelylaan", "authority": "prorail", "status": "aangevraagd", "submission_date": "2024-02-28", "expected_approval": "2024-06-01", "actual_approval": None, "risk_level": "hoog", "auto_detected": True},
]

estimations[seed_id] = {
    "id": "e1",
    "project_id": seed_id,
    "version": 2,
    "hours_engineering": 680,
    "hours_pm": 420,
    "hours_om": 310,
    "hours_workprep": 290,
    "hours_execution": 2500,
    "cost_materials": 680000,
    "cost_total": 1850000,
    "bandwidth_low": 1680000,
    "bandwidth_high": 2150000,
    "confidence_score": 0.74,
    "methodology": "Gewogen analyse op basis van 8 vergelijkbare gasprojecten in Amsterdam (2020-2023). Locatiemultiplier 1.35x (binnenstedelijk). Fase DO: confidentie 74%.",
    "similar_projects": [
        {"name": "Gasleiding Osdorp 2022", "similarity": 0.91, "hours_total": 4050, "cost_total": 1720000},
        {"name": "DN200 Vervangingsproject Geuzenveld 2021", "similarity": 0.87, "hours_total": 3980, "cost_total": 1650000},
        {"name": "Gasnetten Slotermeer 2023", "similarity": 0.83, "hours_total": 4300, "cost_total": 1920000},
    ],
    "reasoning": "Engineering: 680u op basis van 2.4km tracé × 28u/100m (binnenstedelijk). PM: 420u conform DO-fase norm. OM: verhoogd i.v.m. spoorwegkruising en drukke omgeving. Werkvoorbereiding: 290u inclusief KLIC en vergunningdossiers.",
}

# --- Auth ---
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/v1/auth/login")
def login(req: LoginRequest):
    return {
        "access_token": "demo-token-abc123",
        "token_type": "bearer",
        "user": {"id": "u1", "email": req.email, "name": "Demo Gebruiker", "role": "pm", "organization_id": "org-liander"},
    }

@app.post("/api/v1/auth/register")
def register(req: dict):
    return {"access_token": "demo-token-abc123", "token_type": "bearer", "user": {"id": "u2", "email": req.get("email"), "name": req.get("name"), "role": "pm"}}

# --- Projects ---
@app.get("/api/v1/projects")
def list_projects():
    return {"items": list(projects.values()), "total": len(projects)}

@app.post("/api/v1/projects")
def create_project(data: dict):
    pid = str(uuid.uuid4())
    data["id"] = pid
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    data.setdefault("budget_actual", 0)
    data.setdefault("hours_actual", 0)
    projects[pid] = data
    return data

@app.get("/api/v1/projects/{project_id}")
def get_project(project_id: str):
    if project_id not in projects:
        raise HTTPException(404, "Project niet gevonden")
    return projects[project_id]

@app.put("/api/v1/projects/{project_id}")
def update_project(project_id: str, data: dict):
    if project_id not in projects:
        raise HTTPException(404)
    projects[project_id].update(data)
    projects[project_id]["updated_at"] = datetime.now().isoformat()
    return projects[project_id]

# --- Risks ---
@app.get("/api/v1/projects/{project_id}/risks")
def list_risks(project_id: str):
    return risks.get(project_id, [])

@app.post("/api/v1/projects/{project_id}/risks")
def create_risk(project_id: str, data: dict):
    data["id"] = str(uuid.uuid4())
    data["project_id"] = project_id
    data["auto_detected"] = False
    if project_id not in risks:
        risks[project_id] = []
    risks[project_id].append(data)
    return data

@app.post("/api/v1/projects/{project_id}/risks/auto-detect")
def auto_detect_risks(project_id: str):
    return risks.get(project_id, [])

# --- Permits ---
@app.get("/api/v1/projects/{project_id}/permits")
def list_permits(project_id: str):
    return permits.get(project_id, [])

@app.post("/api/v1/projects/{project_id}/permits")
def create_permit(project_id: str, data: dict):
    data["id"] = str(uuid.uuid4())
    data["project_id"] = project_id
    if project_id not in permits:
        permits[project_id] = []
    permits[project_id].append(data)
    return data

@app.post("/api/v1/projects/{project_id}/permits/auto-detect")
def auto_detect_permits(project_id: str):
    return permits.get(project_id, [])

# --- Estimation ---
@app.get("/api/v1/projects/{project_id}/estimation")
def get_estimation(project_id: str):
    if project_id not in estimations:
        raise HTTPException(404, "Nog geen raming beschikbaar")
    return estimations[project_id]

@app.post("/api/v1/projects/{project_id}/estimation/generate")
def generate_estimation(project_id: str, data: dict = {}):
    p = projects.get(project_id, {})
    est = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "version": 1,
        "hours_engineering": 480,
        "hours_pm": 320,
        "hours_om": 240,
        "hours_workprep": 210,
        "hours_execution": 1800,
        "cost_materials": 450000,
        "cost_total": 1200000,
        "bandwidth_low": 1050000,
        "bandwidth_high": 1420000,
        "confidence_score": 0.68,
        "methodology": f"Automatische raming voor {p.get('discipline','onbekend')} project, fase {p.get('phase','VO')}. Op basis van historische benchmarks.",
        "similar_projects": [],
        "reasoning": "Raming gegenereerd op basis van projectparameters en historische data.",
    }
    estimations[project_id] = est
    return est

# --- Historical ---
@app.get("/api/v1/historical")
def list_historical():
    return [
        {"id": "h1", "name": "Gasleiding Osdorp 2022", "discipline": "Gas", "location_type": "urban", "trace_length_m": 2100, "hours_engineering": 620, "cost_total": 1720000, "duration_days": 245},
        {"id": "h2", "name": "DN200 Geuzenveld 2021", "discipline": "Gas", "location_type": "urban", "trace_length_m": 1900, "hours_engineering": 580, "cost_total": 1650000, "duration_days": 210},
        {"id": "h3", "name": "MS-kabel Almere Buiten 2023", "discipline": "Elektra", "location_type": "rural", "trace_length_m": 4500, "hours_engineering": 890, "cost_total": 2340000, "duration_days": 180},
        {"id": "h4", "name": "LS-net uitbreiding Haarlem 2022", "discipline": "LS_MS", "location_type": "urban", "trace_length_m": 800, "hours_engineering": 310, "cost_total": 680000, "duration_days": 95},
    ]

@app.get("/api/v1/historical/similar")
def similar_projects():
    return [
        {"id": "h1", "name": "Gasleiding Osdorp 2022", "similarity_score": 0.91, "hours_engineering": 620, "cost_total": 1720000, "duration_days": 245, "location_type": "urban"},
        {"id": "h2", "name": "DN200 Geuzenveld 2021", "similarity_score": 0.87, "hours_engineering": 580, "cost_total": 1650000, "duration_days": 210, "location_type": "urban"},
    ]

# --- Organization ---
@app.get("/api/v1/organizations/me")
def get_org():
    return {"id": "org-liander", "name": "Liander N.V.", "slug": "liander", "subscription_tier": "professional", "max_projects": 100, "max_users": 50}

@app.get("/api/v1/organizations/me/stats")
def get_org_stats():
    return {"total_projects": 12, "active_projects": 5, "total_hours_estimated": 48200, "total_budget_estimated": 18500000, "open_risks": 23, "pending_permits": 8}

@app.get("/api/v1/organizations/me/users")
def get_org_users():
    return [
        {"id": "u1", "name": "Jan de Vries", "email": "j.devries@liander.nl", "role": "pm"},
        {"id": "u2", "name": "Ingrid Bakker", "email": "i.bakker@liander.nl", "role": "engineer"},
        {"id": "u3", "name": "Marco Smit", "email": "m.smit@liander.nl", "role": "om"},
    ]

# --- GIS ---
@app.post("/api/v1/gis/analyze")
def analyze_gis(data: dict):
    return {"trace_length_m": 2400, "area_type": "urban", "crossings": {"waterways": 1, "major_roads": 3, "railways": 1}, "municipality": "Amsterdam", "natura2000_nearby": False}

@app.post("/api/v1/gis/analyze-pdok")
def analyze_pdok(data: dict):
    return {"municipality": "Amsterdam", "natura2000_nearby": False, "bag_address_density": "hoog", "crossings": {"waterways": 1, "major_roads": 3, "railways": 1, "cycle_paths": 5}, "detected_risks": ["Spoorwegkruising — ProRail afstemming vereist", "Drukke verkeersaders — BABW vergunning nodig"], "likely_permits": ["Instemmingsbesluit", "Verkeersmaatregelen BABW", "Spoorvergunning ProRail"]}

# --- Dashboard ---
@app.get("/api/v1/dashboard/kpis")
def get_kpis():
    return {"total_projects": 12, "active_projects": 5, "budget_total": 18500000, "budget_spent": 8200000, "hours_estimated": 48200, "hours_actual": 21400, "open_risks": 23, "critical_risks": 4, "pending_permits": 8}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
