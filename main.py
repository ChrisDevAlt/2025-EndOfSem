from fastapi import FastAPI, Depends
from fastapi.requests import Request
from fastapi.responses import Response,  HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from validators import AddPatient
from database import DBApi, Patient, Doctor
from typing import Dict
import hashlib
from datetime import datetime, timedelta

## 
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")
db = DBApi(patients=Patient, doctors=Doctor)
app.mount("/images", StaticFiles(directory="images"), name="static")

async def check_session(request: Request):
    id = request.cookies.get("identifier")
    if not id:
        return {"success": False}
    return {"success": True, "id":id}
        


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, commonDep: dict = Depends(check_session)):
    if commonDep["success"] == False:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    print(commonDep)
    patients = db.get_patients(commonDep["id"])
    doctor = db.get_doctor(id=commonDep["id"], email=None)
    mostRecent = patients[:6:-1] if len(patients) >= 7 else patients[::-1]
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"username": doctor.name, "total_patients":len(patients), "recentPatients":mostRecent if mostRecent else []})


@app.get("/view_patients", response_class=HTMLResponse)
async def view_patients(request: Request, commonDep: dict = Depends(check_session)):
    if commonDep["success"] == False:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    return templates.TemplateResponse(request=request, name="view_patients.html", context={"patientsList": db.get_patients(commonDep["id"])})

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request, commonDep: dict = Depends(check_session)):
    if commonDep["success"] == False:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    return templates.TemplateResponse(request=request, name="settings.html", context={})

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, commonDep: dict = Depends(check_session)):
    if commonDep["success"] == True:
        return templates.TemplateResponse(request=request, name="dashboard.html", context={})
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/add_patient", response_class=HTMLResponse)
async def serve_add_patient(request: Request, commonDep: dict = Depends(check_session)):
    """
    This will server the add patient html file
    """
    if commonDep["success"] == False:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    return templates.TemplateResponse(request=request, name="add_patient.html")

@app.get("/delete_patient/{id}")
async def delete_patient(id: str,request: Request, commonDep: dict = Depends(check_session)):
    if commonDep["success"] == False:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    res = db.delete_patient(id=id)
    if not res:
        return False
    return True

@app.post("/add_patient")
async def add_patient(data: AddPatient, request: Request):
    """
    Adding patients to db
    """
    id = request.cookies.get("identifier")
    if not id:
        return {"succses": False}
    res = db.add_patient(name=data.name, age=data.age, condition=data.condition, contact=data.phone, note=data.notes, gender=data.gender, doctor=id)
    return {"success": True if res == True else False}


@app.post("/login")
async def login(cred: Dict[str, str],response: Response):
    result = db.get_doctor(email=cred["email"], id=None)
    if hashlib.sha256(cred["password"].encode("utf-8")).hexdigest() != result.password:
        return {"success": False}
    expiry_time = datetime.utcnow()+timedelta(hours=2)
    response.set_cookie("identifier", result.id, expires=expiry_time.strftime("%a %d %b %Y %H:%M:%S GMT"), httponly=True, secure=True, samesite="lax")
    return {"success": True}

@app.get("/logout")
async def logout(response: Response, request: Request):
    response.delete_cookie(key="identifier", httponly=True, secure=True, samesite="lax")
    return templates.TemplateResponse(request=request, name="index.html", context={})