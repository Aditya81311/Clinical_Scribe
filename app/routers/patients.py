from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor, Patient
from app.auth import require_doctor_page
from app.templating import templates

router = APIRouter()


@router.get("/patients")
def list_patients(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    doctor: Doctor = Depends(require_doctor_page),
):
    query = db.query(Patient).filter(Patient.doctor_id == doctor.id)
    if q:
        query = query.filter(Patient.name.ilike(f"%{q}%"))
    patients = query.order_by(Patient.created_at.desc()).all()

    ctx = {"doctor": doctor, "patients": patients, "q": q, "active": "patients"}
    if request.headers.get("HX-Request") == "true" and request.headers.get("HX-Target") == "patients-table":
        return templates.TemplateResponse(request, "patients/_table.html", ctx)
    return templates.TemplateResponse(request, "patients/list.html", ctx)


@router.post("/patients")
def create_patient(
    request: Request,
    db: Session = Depends(get_db),
    doctor: Doctor = Depends(require_doctor_page),
    name: str = Form(...),
    age: str = Form(""),
    gender: str = Form(""),
    phone: str = Form(""),
    notes: str = Form(""),
):
    patient = Patient(
        doctor_id=doctor.id,
        name=name.strip(),
        age=int(age) if age.strip().isdigit() else None,
        gender=gender or None,
        phone=phone.strip() or None,
        notes=notes.strip() or None,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    patients = (
        db.query(Patient)
        .filter(Patient.doctor_id == doctor.id)
        .order_by(Patient.created_at.desc())
        .all()
    )
    response = templates.TemplateResponse(
        request, "patients/_table.html", {"doctor": doctor, "patients": patients, "q": ""}
    )
    response.headers["HX-Trigger"] = "patient-added"
    return response


@router.get("/patients/{patient_id}")
def patient_detail(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    doctor: Doctor = Depends(require_doctor_page),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.doctor_id == doctor.id)
        .first()
    )
    if not patient:
        raise HTTPException(404, "Patient not found")

    return templates.TemplateResponse(request, "patients/detail.html", {
        "doctor": doctor,
        "patient": patient,
        "consultations": patient.consultations,
        "active": "patients",
    })
