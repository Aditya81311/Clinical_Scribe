import json
import os
import traceback
import uuid

from fastapi import APIRouter, Request, UploadFile, File, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Doctor, Patient, Consultation
from app.config import UPLOAD_DIR
from app.auth import require_doctor_page
from app.services.transcription import transcribe_audio
from app.services.extraction import extract_clinical_data
from app.templating import templates

router = APIRouter()


def run_pipeline(consultation_id: int):
    db = SessionLocal()
    c = db.query(Consultation).get(consultation_id)
    try:
        segments = transcribe_audio(c.filename)
        c.raw_transcript = "\n".join(s["text"] for s in segments)
        db.commit()

        result = extract_clinical_data(segments)
        if not isinstance(result, dict):
            raise ValueError(f"extract_clinical_data returned {type(result)}, expected dict")
        c.result_json = json.dumps(result)
        c.primary_diagnosis = (result.get("primary_diagnosis") or "Unspecified").strip() or "Unspecified"
        c.status = "done"
    except Exception as e:
        c.status = "failed"
        c.error = f"{e}\n{traceback.format_exc()}"
    db.commit()
    db.close()


@router.post("/patients/{patient_id}/consultations")
async def create_consultation(
    patient_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    doctor: Doctor = Depends(require_doctor_page),
    file: UploadFile = File(...),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.doctor_id == doctor.id)
        .first()
    )
    if not patient:
        raise HTTPException(404, "Patient not found")

    ext = os.path.splitext(file.filename or "")[1] or ".wav"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest_path, "wb") as f:
        f.write(await file.read())

    c = Consultation(
        doctor_id=doctor.id,
        patient_id=patient.id,
        filename=dest_path,
        original_name=file.filename,
        status="processing",
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    background_tasks.add_task(run_pipeline, c.id)

    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = f"/consultations/{c.id}"
        return response
    return RedirectResponse(f"/consultations/{c.id}", status_code=303)


@router.get("/consultations/{consultation_id}")
def consultation_page(
    consultation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    doctor: Doctor = Depends(require_doctor_page),
):
    c = (
        db.query(Consultation)
        .filter(Consultation.id == consultation_id, Consultation.doctor_id == doctor.id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Consultation not found")

    file_url = None
    try:
        file_url = f"/uploads/{os.path.basename(c.filename)}" if c.filename else None
    except Exception:
        file_url = None
    return templates.TemplateResponse(request, "consultations/detail.html", {
        "doctor": doctor,
        "consultation": c,
        "patient": c.patient,
        "file_url": file_url,
        "active": "patients",
    })


@router.get("/consultations/{consultation_id}/status-partial")
def consultation_status_partial(
    consultation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    doctor: Doctor = Depends(require_doctor_page),
):
    c = (
        db.query(Consultation)
        .filter(Consultation.id == consultation_id, Consultation.doctor_id == doctor.id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Consultation not found")

    if c.status == "processing":
        # Nothing changed yet — 204 means htmx won't touch the DOM at all,
        # so the waveform/skeleton animation keeps running instead of restarting.
        return Response(status_code=204)
    result = json.loads(c.result_json) if c.result_json else None
    file_url = None
    try:
        file_url = f"/uploads/{os.path.basename(c.filename)}" if c.filename else None
    except Exception:
        file_url = None
    return templates.TemplateResponse(request, "consultations/_status.html", {
        "consultation": c,
        "result": result,
        "file_url": file_url,
    })
