"""
One LLM call takes the raw (speaker-less) Whisper transcript and returns:
  - speaker-labeled transcript (Doctor/Patient, inferred from content)
  - structured clinical fields
  - SOAP note
  - action item list

Combining these into one call (instead of separate diarization + extraction
steps) saves both build time and tokens, and is one of the two documented
options for speaker attribution (see services/diarization.py for the other).
"""
import json
import time
import requests
from requests.exceptions import HTTPError
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL

SYSTEM_PROMPT = """You are a clinical scribe assistant for Indian multilingual \
(English/Hindi/Hinglish, code-switched) doctor-patient consultations.

You will receive a raw speech-to-text transcript as timestamped segments, \
with NO speaker labels. Your job:

1. Infer which segments are the Doctor vs the Patient from conversational \
content (the doctor asks questions/gives instructions; the patient describes \
symptoms/answers). Merge consecutive same-speaker segments into turns.
2. Extract clinically relevant information, in English, even if the source \
was in Hindi/Hinglish.
3. Only use information explicitly present or clearly implied in the \
transcript. Never invent vitals, findings, or history that weren't mentioned.
4. If a field has no information in the transcript, use an empty string or \
empty list — do not guess.
5. "primary_diagnosis" is a SHORT (1-3 word) clinical category label used \
for dashboard analytics, e.g. "Viral Fever", "Hypertension", "Type 2 \
Diabetes", "URI", "Gastroenteritis". Base it on the doctor's stated \
assessment/impression if present, otherwise your best short label for the \
chief complaint. If genuinely nothing can be inferred, use "Unspecified".

Return ONLY valid JSON matching exactly this schema, no markdown fences, no \
commentary:

{
  "speaker_transcript": [{"speaker": "Doctor"|"Patient", "text": "..."}],
  "chief_complaint": "string",
  "primary_diagnosis": "string",
  "symptoms": ["string"],
  "history": "string",
  "medications": ["string"],
  "investigations": ["string"],
  "soap": {
    "subjective": "string",
    "objective": "string",
    "assessment": "string",
    "plan": "string"
  },
  "action_items": ["string"]
}
"""


def _post_with_retries(url, headers, payload, timeout=60, max_retries=5):
    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 429:
                # honor Retry-After if provided
                retry_after = r.headers.get("Retry-After")
                try:
                    wait = float(retry_after) if retry_after is not None else backoff
                except Exception:
                    wait = backoff
                time.sleep(wait)
                backoff = min(backoff * 2, 60)
                continue
            r.raise_for_status()
            return r
        except HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status and 500 <= status < 600 and attempt < max_retries:
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            raise



def extract_clinical_data(segments: list[dict]) -> dict:
    transcript_text = "\n".join(
        f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments
    )
    try:
        resp = _post_with_retries(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        payload={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript_text},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        },
        timeout=60,
    )
    except Exception as e:
        # If the LLM service is rate-limited or failing, return a minimal
        # safe fallback so the app can continue for a demo.
        combined = "\n".join(t['text'] for t in segments)
        return {
            "speaker_transcript": [{"speaker": "Unknown", "text": combined}],
            "chief_complaint": "",
            "primary_diagnosis": "Unspecified",
            "symptoms": [],
            "history": "",
            "medications": "",
            "investigations": "",
            "soap": {"subjective": "", "objective": "", "assessment": "", "plan": ""},
            "action_items": [],
        }
    content = resp.json()["choices"][0]["message"]["content"]

    # some models wrap JSON in ```json fences despite instructions — strip defensively
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        content = content[4:] if content.startswith("json") else content

    print("RAW EXTRACTION CONTENT:", content[:2000])  # TEMP DEBUG — remove later

    parsed = json.loads(content)

    if isinstance(parsed, list):
        parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}

    if not isinstance(parsed, dict):
        raise ValueError(f"Extraction returned unexpected JSON shape: {type(parsed)}")

    return parsed


def answer_question(segments: list[dict], result: dict, question: str) -> str:
    """Optional feature: clinical Q&A over the consultation."""
    transcript_text = "\n".join(
        f"{t['speaker']}: {t['text']}" for t in result.get("speaker_transcript", [])
    )
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Answer the question using ONLY the consultation "
                "transcript below. If the answer isn't in it, say so.\n\n"
                + transcript_text,
            },
            {"role": "user", "content": question},
        ],
        "temperature": 0.1,
    }

    resp = _post_with_retries(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        payload=payload,
        timeout=60,
    )

    return resp.json()["choices"][0]["message"]["content"]
