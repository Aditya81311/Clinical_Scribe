from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor, Patient, Consultation
from app.auth import require_doctor_page
from app.templating import templates

router = APIRouter()

AGE_BUCKETS = [
    ("0-12", 0, 12),
    ("13-18", 13, 18),
    ("19-35", 19, 35),
    ("36-50", 36, 50),
    ("51-65", 51, 65),
    ("65+", 66, 200),
]


@router.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    from app.auth import get_optional_doctor
    if get_optional_doctor(request, db):
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/login", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), doctor: Doctor = Depends(require_doctor_page)):
    patients = db.query(Patient).filter(Patient.doctor_id == doctor.id).all()
    consultations = (
        db.query(Consultation)
        .filter(Consultation.doctor_id == doctor.id)
        .order_by(Consultation.created_at.desc())
        .all()
    )

    total_patients = len(patients)
    total_consultations = len(consultations)

    week_ago = datetime.utcnow() - timedelta(days=7)
    consultations_this_week = sum(1 for c in consultations if c.created_at and c.created_at >= week_ago)

    diagnosis_counts = Counter(
        c.primary_diagnosis for c in consultations
        if c.primary_diagnosis and c.primary_diagnosis.lower() != "unspecified"
    )
    top_diagnoses = diagnosis_counts.most_common(6)
    most_common_diagnosis = top_diagnoses[0][0] if top_diagnoses else "—"

    # Age distribution across patients
    age_bucket_counts = {label: 0 for label, _, _ in AGE_BUCKETS}
    for p in patients:
        if p.age is None:
            continue
        for label, lo, hi in AGE_BUCKETS:
            if lo <= p.age <= hi:
                age_bucket_counts[label] += 1
                break

    # Diagnoses-by-age-bucket, for the "disease per age" chart: for each age
    # bucket, which diagnosis showed up most.
    patient_age_by_id = {p.id: p.age for p in patients}
    bucket_diagnosis_counts = {label: Counter() for label, _, _ in AGE_BUCKETS}
    for c in consultations:
        if not c.primary_diagnosis or c.primary_diagnosis.lower() == "unspecified":
            continue
        age = patient_age_by_id.get(c.patient_id)
        if age is None:
            continue
        for label, lo, hi in AGE_BUCKETS:
            if lo <= age <= hi:
                bucket_diagnosis_counts[label][c.primary_diagnosis] += 1
                break

    top_dx_labels = [d for d, _ in top_diagnoses] or ["No data yet"]
    disease_age_series = []
    for dx in ([d for d, _ in top_diagnoses] or []):
        disease_age_series.append({
            "label": dx,
            "data": [bucket_diagnosis_counts[label][dx] for label, _, _ in AGE_BUCKETS],
        })

    recent_consultations = consultations[:6]

    return templates.TemplateResponse(request, "dashboard.html", {
        "doctor": doctor,
        "active": "dashboard",
        "total_patients": total_patients,
        "total_consultations": total_consultations,
        "consultations_this_week": consultations_this_week,
        "most_common_diagnosis": most_common_diagnosis,
        "age_labels": [label for label, _, _ in AGE_BUCKETS],
        "age_counts": [age_bucket_counts[label] for label, _, _ in AGE_BUCKETS],
        "top_diagnosis_labels": [d for d, _ in top_diagnoses],
        "top_diagnosis_counts": [n for _, n in top_diagnoses],
        "disease_age_series": disease_age_series,
        "recent_consultations": recent_consultations,
    })
