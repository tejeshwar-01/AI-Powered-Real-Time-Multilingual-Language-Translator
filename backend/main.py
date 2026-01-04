import os
import json
import re
import numpy as np
import torch
import whisper
import anyio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ======================================================
# APP SETUP
# ======================================================
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)

# ======================================================
# DEVICE
# ======================================================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Running on: {device}")

# ======================================================
# WHISPER (Speech → Text)
# ======================================================
print("🔊 Loading Whisper (small)...")
whisper_model = whisper.load_model("small", device=device)
whisper_model.eval()

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.35
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

def whisper_infer(audio_chunk: np.ndarray):
    with torch.no_grad():
        result = whisper_model.transcribe(
            audio_chunk,
            fp16=(device == "cuda"),
            language=None
        )

    text = result.get("text", "").strip()
    if not text or len(text) < 3:
        return None

    src_lang = result.get("language", "en")
    segments = result.get("segments", [])

    confidence = (
        round(sum(s.get("avg_logprob", 0.0) for s in segments) / len(segments), 2)
        if segments else 0.0
    )

    return text, src_lang, confidence

# ======================================================
# TRANSLATION (NLLB-200 – FREE)
# ======================================================
print("🌍 Loading NLLB-200 (Telugu & Tamil supported)...")

MODEL_NAME = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
translator = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
translator.eval()

LANG_MAP = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "te": "tel_Telu",
    "ta": "tam_Taml",
    "es": "spa_Latn",
    "de": "deu_Latn",
}

def translate_infer(text: str, src_lang: str, tgt_lang: str):
    src = LANG_MAP.get(src_lang, "eng_Latn")
    tgt = LANG_MAP.get(tgt_lang, "eng_Latn")

    if src == tgt:
        return text

    tokenizer.src_lang = src

    encoded = tokenizer(
        text,
        return_tensors="pt",
        padding=True
    ).to(device)

    with torch.no_grad():
        output = translator.generate(
            **encoded,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt),
            max_length=128,
            num_beams=5,
            length_penalty=1.2,
            early_stopping=True
        )

    return tokenizer.batch_decode(output, skip_special_tokens=True)[0]

# ======================================================
# GRAMMAR POLISHING (RULE-BASED)
# ======================================================
def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def polish_telugu(text: str) -> str:
    rules = {
        "తినడానికి కావలసిన": "తినాలని ఉంది",
        "తినడానికి": "తినాలని ఉంది",
        "నేను కావాలి": "నాకు కావాలి",
        "నేను అవసరం": "నాకు అవసరం",
        "నేను వెళ్లడానికి": "నాకు వెళ్లాలని ఉంది",
        "నేను కోరుకుంటున్నాను": "నాకు కావాలి",
    }
    for k, v in rules.items():
        text = text.replace(k, v)

    if not text.endswith(("ఉంది", "కావాలి", "అనుకుంటున్నాను")):
        text += "."

    return normalize(text)

def polish_tamil(text: str) -> str:
    rules = {
        "சாப்பிட வேண்டும்": "சாப்பிட விரும்புகிறேன்",
        "நான் வேண்டும்": "எனக்கு வேண்டும்",
        "செல்ல வேண்டும்": "செல்ல விரும்புகிறேன்",
    }
    for k, v in rules.items():
        text = text.replace(k, v)

    if not text.endswith(("விரும்புகிறேன்", "வேண்டும்")):
        text += "."

    return normalize(text)

def polish_hindi(text: str) -> str:
    rules = {
        "मैं चाहिए": "मुझे चाहिए",
        "खाने के लिए चाहिए": "खाना चाहता हूँ",
    }
    for k, v in rules.items():
        text = text.replace(k, v)

    return normalize(text)

# ======================================================
# WEBSOCKET (TEXT + VOICE)
# ======================================================
@app.websocket("/ws/stream")
async def websocket_stream(ws: WebSocket):
    await ws.accept()
    print("✅ WebSocket connected")

    pcm_buffer = np.zeros(0, dtype=np.float32)
    target_lang = "hi"

    try:
        while True:
            msg = await ws.receive()

            if msg.get("type") == "websocket.disconnect":
                break

            # ---------- TEXT ----------
            if "text" in msg and msg["text"]:
                data = json.loads(msg["text"])

                if data.get("type") == "config":
                    target_lang = data.get("lang", target_lang)

                elif data.get("type") == "text_translate":
                    translated = await anyio.to_thread.run_sync(
                        translate_infer,
                        data["text"],
                        "en",
                        target_lang
                    )

                    if target_lang == "te":
                        translated = polish_telugu(translated)
                    elif target_lang == "ta":
                        translated = polish_tamil(translated)
                    elif target_lang == "hi":
                        translated = polish_hindi(translated)

                    await ws.send_json({
                        "original": data["text"],
                        "translated": translated,
                        "source_lang": "en",
                        "confidence": 1.0
                    })

            # ---------- VOICE ----------
            elif "bytes" in msg and msg["bytes"]:
                audio = (
                    np.frombuffer(msg["bytes"], dtype=np.int16)
                    .astype(np.float32) / 32768.0
                )

                pcm_buffer = np.concatenate([pcm_buffer, audio])

                if len(pcm_buffer) >= CHUNK_SIZE:
                    chunk = pcm_buffer[:CHUNK_SIZE]
                    pcm_buffer = pcm_buffer[CHUNK_SIZE:]

                    result = await anyio.to_thread.run_sync(
                        whisper_infer, chunk
                    )

                    if not result:
                        continue

                    text, src_lang, confidence = result

                    translated = await anyio.to_thread.run_sync(
                        translate_infer,
                        text,
                        src_lang,
                        target_lang
                    )

                    if target_lang == "te":
                        translated = polish_telugu(translated)
                    elif target_lang == "ta":
                        translated = polish_tamil(translated)
                    elif target_lang == "hi":
                        translated = polish_hindi(translated)

                    await ws.send_json({
                        "original": text,
                        "translated": translated,
                        "source_lang": src_lang,
                        "confidence": confidence
                    })

    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        print("🔌 WebSocket closed safely")
