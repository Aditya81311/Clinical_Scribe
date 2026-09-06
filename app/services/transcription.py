"""
Uses your fine-tuned Whisper checkpoint (WhisperProcessor + WhisperForConditionalGeneration)
instead of openai-whisper. Since transformers doesn't auto-chunk with timestamps like
openai-whisper does, this uses the HF `pipeline` wrapper with chunk_length_s so the output
still comes back as [{start, end, text}, ...] — same shape extraction.py expects.

Note: your original model.py forced language="en" during generate(). Removed that here
since this pipeline needs to handle Hindi/Hinglish too. Add it back via generate_kwargs
if your checkpoint was fine-tuned English-only and code-switching accuracy suffers without it.
"""
import os
import librosa
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline
from app.config import MODEL_PATH

_pipe = None


def _get_pipeline():
    global _pipe
    if _pipe is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model path '{MODEL_PATH}' does not exist.")

        processor = WhisperProcessor.from_pretrained(MODEL_PATH)
        model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH)
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device_str)
        print(f"Using device: {device_str}")

        _pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            chunk_length_s=30,
            stride_length_s=5,
            device=0 if device_str == "cuda" else -1,
        )
    return _pipe


def transcribe_audio(audio_path: str) -> list[dict]:
    """Returns [{start: float, end: float, text: str}, ...]"""
    audio_data, _ = librosa.load(audio_path, sr=16000, mono=True)
    audio_data = librosa.util.normalize(audio_data)
    audio_data, _ = librosa.effects.trim(audio_data, top_db=20)

    pipe = _get_pipeline()
    output = pipe(
        audio_data,
        return_timestamps=True,
        generate_kwargs={"num_beams": 4, "no_repeat_ngram_size": 2},
    )

    segments = []
    for chunk in output["chunks"]:
        start, end = chunk["timestamp"]
        segments.append({
            "start": start or 0.0,
            "end": end if end is not None else (start or 0.0),
            "text": chunk["text"].strip(),
        })
    return segments
