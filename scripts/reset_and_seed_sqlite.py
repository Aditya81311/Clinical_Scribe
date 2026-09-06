#!/usr/bin/env python3
"""Reset patients/consultations and seed dummy patients using sqlite3 (no external deps).
"""
import sqlite3
import random
from datetime import datetime

DB = '/mnt/New_Folder/Clinical_Scribe/V2/scribe.db'
DOCTOR_EMAIL = 'aditya81311@gmail.com'

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
]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print('Deleting consultations and patients...')
    cur.execute('DELETE FROM consultations')
    cur.execute('DELETE FROM patients')
    conn.commit()

    cur.execute('SELECT id FROM doctors WHERE email = ?', (DOCTOR_EMAIL,))
    row = cur.fetchone()
    if row:
        doctor_id = row['id']
        print(f'Found doctor id={doctor_id} for {DOCTOR_EMAIL}')
    else:
        print(f'Doctor with email {DOCTOR_EMAIL} not found. Creating placeholder account...')
        cur.execute('INSERT INTO doctors (name,email,password_hash,specialization,created_at) VALUES (?,?,?,?,?)',
                    ('Aditya', DOCTOR_EMAIL, '', 'General', datetime.utcnow().isoformat()))
        conn.commit()
        doctor_id = cur.lastrowid
        print('Created doctor id=', doctor_id)

    print('Seeding patients...')
    for i, name in enumerate(names, start=1):
        age = random.randint(18, 80)
        gender = random.choice(['Male', 'Female', 'Other'])
        phone = f'9{random.randint(600000000, 999999999)}'
        notes = f'Dummy patient #{i} seeded on {datetime.utcnow().isoformat()}'
        cur.execute(
            'INSERT INTO patients (doctor_id,name,age,gender,phone,notes,created_at) VALUES (?,?,?,?,?,?,?)',
            (doctor_id, name, age, gender, phone, notes, datetime.utcnow().isoformat()),
        )

    conn.commit()
    print(f'Inserted {len(names)} patients for doctor id={doctor_id}')
    conn.close()


if __name__ == '__main__':
    main()
