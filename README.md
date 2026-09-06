# Ambient AI Clinical Scribe

Ambient AI clinical documentation for Indian multilingual (English/Hindi/Hinglish)
doctor–patient consultations — upload a recording, get back a structured chart
note with speaker-attributed transcript, chief complaint, symptoms, history,
medications, investigations, a SOAP note and an action summary.

This build extends the original transcription+extraction prototype with doctor
accounts, patient records, and a clinic-facing dashboard, and replaces the
placeholder UI with a Jinja2 + Tailwind + HTMX + Alpine.js frontend.

## What's included

**Accounts**
- Doctor sign up / log in / log out (session-cookie based, passwords hashed with PBKDF2)
- Every patient and consultation is scoped to the logged-in doctor

**Patients**
- Add a patient (name, age, gender, phone, notes)
- Live search across your patient roster (HTMX, no page reload)
- Patient detail page with a chronological consultation timeline

**Consultations**
- Upload a recorded consultation against a specific patient
- Background pipeline: speech-to-text → speaker + clinical extraction (your
  existing Whisper checkpoint + OpenRouter LLM call, unchanged)
- Live status polling with an audio-waveform processing animation — no
  manual refresh, and you can navigate away and come back
- Full chart note view: chief complaint, symptoms, history, medications,
  investigations, SOAP note, action summary, and the color-coded
  Doctor/Patient transcript

**Dashboard**
- Total patients, total consultations, consultations this week, most common diagnosis
- Patients-by-age-group chart
- Most-common-diagnoses chart
- Diagnoses-by-age-group breakdown (which conditions show up in which age bands)
- Recent consultations list

## Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Frontend:** Jinja2 templates, Tailwind (CDN), HTMX for partial updates
  (search, add-patient, consultation upload + status polling), Alpine.js for
  modals/interactivity
- **Charts:** Chart.js
- **Auth:** Starlette `SessionMiddleware` + `passlib` (PBKDF2-SHA256)

## Project structure

```
app/
  main.py                 FastAPI app, middleware, routers
  config.py               Env-driven config (model path, OpenRouter key, DB, etc.)
  database.py             SQLAlchemy engine/session
  models.py               Doctor, Patient, Consultation
  schemas.py              Pydantic request/response models
  auth.py                 Password hashing + session helpers/dependencies
  templating.py           Shared Jinja2Templates instance + filters
  routers/
    auth.py               /signup, /login, /logout
    dashboard.py           /, /dashboard
    patients.py            /patients, /patients/{id}
    consultations.py       consultation upload + status/result endpoints
  services/
    transcription.py       Whisper checkpoint → timestamped segments (unchanged)
    extraction.py           LLM call → speaker transcript + structured fields
    diarization.py          Notes on optional acoustic diarization (unused by default)
  templates/               Jinja2 templates (see below)
  static/css/app.css        Design tokens + animations (waveform, shimmer, transitions)
uploads/                   Uploaded consultation audio files
requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` in the project root (same variables as before):

```
OPENROUTER_API_KEY=sk-...
OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
MODEL_PATH=/path/to/your/whisper_finetuned/final_model
SESSION_SECRET_KEY=change-me-to-something-random
```

Run it:

```bash
uvicorn app.main:app --reload
```

Then open `http://localhost:8000` — you'll be redirected to sign up.

## Notes on the extraction schema

`primary_diagnosis` was added to the LLM extraction schema (a short 1–3 word
label like "Viral Fever" or "Type 2 Diabetes") purely to power the dashboard's
diagnosis charts. It's cached onto the `Consultation` row (`primary_diagnosis`
column) at pipeline completion so dashboard aggregation doesn't need to
re-parse `result_json` for every consultation on every page load.

## Deliberately left out

To keep the surface area small and the codebase easy to defend in a demo, a
few things from the original prototype were intentionally dropped rather than
wired into the new UI:

- The free-text "ask a question about this consultation" endpoint
  (`services/extraction.answer_question`) — the function is still there if
  you want to add a Q&A panel later, it's just not exposed in the UI.
- Acoustic (pyannote) diarization — speaker attribution is still done by the
  LLM from conversational content, as in the original design; see
  `services/diarization.py` for how to swap in real diarization later.
