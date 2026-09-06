from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models import Doctor

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def login_doctor(request: Request, doctor_id: int) -> None:
    request.session["doctor_id"] = doctor_id


def logout_doctor(request: Request) -> None:
    request.session.clear()


def get_optional_doctor(request: Request, db: Session = Depends(get_db)) -> Doctor | None:
    doctor_id = request.session.get("doctor_id")
    if not doctor_id:
        return None
    return db.query(Doctor).get(doctor_id)


def require_doctor_page(request: Request, db: Session = Depends(get_db)) -> Doctor:
    """Dependency for HTML page routes. Raises a redirect-friendly 401 that
    the exception handler turns into a redirect to /login."""
    doctor = get_optional_doctor(request, db)
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return doctor


def require_doctor_api(request: Request, db: Session = Depends(get_db)) -> Doctor:
    doctor = get_optional_doctor(request, db)
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return doctor
