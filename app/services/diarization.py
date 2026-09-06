"""
NOT used by the default pipeline. Speaker attribution is currently done by
the LLM in extraction.py, based on conversational content (who's asking vs
who's describing symptoms) — this is faster to ship and often more accurate
than timestamp-based diarization on short, single-channel demo clips.

If you want real acoustic diarization later, implement it here:

    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=HF_TOKEN
    )
    diarization = pipeline(audio_path)
    # yields (segment, _, speaker_label) tuples — merge with whisper
    # segments by timestamp overlap, then map speaker_label -> Doctor/Patient
    # (pyannote gives you SPEAKER_00/01, not role names, so you still need
    # a heuristic or LLM pass to assign roles).

Then call this from routers/consultations.py instead of relying on
extraction.py's content-based labeling.
"""
