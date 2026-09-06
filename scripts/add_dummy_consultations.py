#!/usr/bin/env python3
"""Insert a sample clinical consultation record for each patient of the given doctor.

Usage: python3 scripts/add_dummy_consultations.py
"""
import json
import sqlite3
from datetime import datetime

DB = '/mnt/New_Folder/Clinical_Scribe/V2/scribe.db'
DOCTOR_EMAIL = 'aditya81311@gmail.com'


def make_result(patient_name):
    result = {
        "chief_complaint": "Fever and body ache",
        "symptoms": ["Fever", "Generalized weakness", "Headache"],
        "history": "Onset 3 days ago. Paracetamol tried without relief.",
        "medications": ["Paracetamol 500mg"],
        "investigations": ["CBC", "RBS"],
        "soap": {
            "subjective": "Patient reports fever and malaise",
            "objective": "T: 101F, HR 88",
            "assessment": "Likely viral febrile illness",
            "plan": "Symptomatic care, follow up in 48 hours"
        },
        "action_items": ["Advise rest", "Prescribe paracetamol"],
        "speaker_transcript": [
            {"speaker": "Doctor", "text": "How long have you had fever?"},
            {"speaker": "Patient", "text": "Three days, no improvement with medicine."}
        ]
    }
    return result


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('SELECT id FROM doctors WHERE email = ?', (DOCTOR_EMAIL,))
    row = cur.fetchone()
    if not row:
        print('Doctor not found:', DOCTOR_EMAIL)
        return
    doctor_id = row['id']

    cur.execute('SELECT id, name FROM patients WHERE doctor_id = ?', (doctor_id,))
    patients = cur.fetchall()
    if not patients:
        print('No patients found for doctor id', doctor_id)
        return

    for p in patients:
        patient_id = p['id']
        name = p['name']
        result = make_result(name)
        raw = ' '.join([seg['text'] for seg in result['speaker_transcript']])
        result_json = json.dumps(result)
        primary = result['assessment'] if 'assessment' in result else result['soap'].get('assessment')
        created_at = datetime.utcnow().isoformat()

        cur.execute(
            'INSERT INTO consultations (doctor_id, patient_id, filename, original_name, status, error, raw_transcript, result_json, primary_diagnosis, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (
                doctor_id,
                patient_id,
                'dummy.wav',
                'dummy.wav',
                'done',
                None,
                raw,
                result_json,
                primary or 'Unspecified',
                created_at,
            )
        )

    conn.commit()
    print(f'Inserted consultations for {len(patients)} patients (doctor id={doctor_id})')
    conn.close()


if __name__ == '__main__':
    main()
