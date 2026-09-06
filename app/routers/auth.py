from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor
from app.auth import hash_password, verify_password, login_doctor, logout_doctor, get_optional_doctor
from app.templating import templates

router = APIRouter()


@router.get("/signup")
def signup_page(request: Request, db: Session = Depends(get_db)):
    if get_optional_doctor(request, db):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request, "auth/signup.html", {})


@router.post("/signup")
def signup_submit(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    specialization: str = Form(""),
):
    email = email.strip().lower()
    error = None
    if len(password) < 6:
        error = "Password must be at least 6 characters."
    elif password != confirm_password:
        error = "Passwords do not match."
    elif db.query(Doctor).filter(Doctor.email == email).first():
        error = "An account with this email already exists."

    if error:
        return templates.TemplateResponse(
            request, "auth/signup.html",
            {"error": error, "name": name, "email": email, "specialization": specialization},
            status_code=400,
        )

    doctor = Doctor(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
        specialization=specialization.strip() or None,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    login_doctor(request, doctor.id)
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_optional_doctor(request, db):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html", {})


@router.post("/login")
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    email = email.strip().lower()
    doctor = db.query(Doctor).filter(Doctor.email == email).first()
    if not doctor or not verify_password(password, doctor.password_hash):
        return templates.TemplateResponse(
            request, "auth/login.html",
            {"error": "Invalid email or password.", "email": email},
            status_code=400,
        )

    login_doctor(request, doctor.id)
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/logout")
def logout(request: Request):
    logout_doctor(request)
    return RedirectResponse("/login", status_code=303)
