#!/usr/bin/env python3
"""Reset patient/consultation data and seed dummy patients.

Usage: python scripts/reset_and_seed.py
"""
import random
from datetime import datetime

from app.database import SessionLocal
from app.models import Doctor, Patient, Consultation
from app.auth import hash_password


def seed():
    db = SessionLocal()
    try:
        print("Deleting consultations...")
        db.query(Consultation).delete()
        print("Deleting patients...")
        db.query(Patient).delete()
        db.commit()

        email = "aditya81311@gmail.com"
        print(f"Ensuring doctor account for {email}...")
        doctor = db.query(Doctor).filter(Doctor.email == email).first()
        if not doctor:
            doctor = Doctor(
                name="Aditya",
                email=email,
                password_hash=hash_password("password123"),
                specialization="General",
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            print(f"Created doctor id={doctor.id}")
        else:
            doctor.name = "Aditya"
            doctor.password_hash = hash_password("password123")
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            print(f"Updated doctor id={doctor.id}")

        names = [
            "Aarav Kumar",
            "Isha Sharma",
            "Rohan Patel",
            "Priya Singh",
            "Vikram Rao",
            "Neha Gupta",
            "Karan Mehta",
            "Sana Khan",
            "Arjun Das",
            "Maya Iyer",
            "Ritu Verma",
            "Anil Joshi",
            "Tara Menon",
            "Dev Bhatt",
            "Leena Nair",
        ]

        print("Seeding patients...")
        for i, name in enumerate(names[:12], start=1):
            age = random.randint(18, 80)
            gender = random.choice(["Male", "Female", "Other"])
            phone = f"9{random.randint(600000000, 999999999)}"
            notes = f"Dummy patient #{i} seeded on {datetime.utcnow().isoformat()}"
            p = Patient(
                doctor_id=doctor.id,
                name=name,
                age=age,
                gender=gender,
                phone=phone,
                notes=notes,
            )
            db.add(p)

        db.commit()
        print(f"Inserted {len(names[:12])} patients for doctor id={doctor.id}")
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
