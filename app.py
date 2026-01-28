import os
import uuid
import shutil
import asyncio
import subprocess
import torch
import whisper

from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ================= APP =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DEVICE =================
device = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_grad_enabled(False)
print("🚀 Device:", device)

# ================= MODELS =================
whisper_model = whisper.load_model("base", device=device)

MODEL_NAME = "facebook/m2m100_418M"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
translator = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
translator.eval()

# ================= FRONTEND =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# ================= HELPERS =================
def convert_to_wav(input_path: str, output_path: str):
    """
    Converts any audio to 16kHz mono WAV (Whisper compatible)
    """
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            output_path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

async def whisper_transcribe(path: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, whisper_model.transcribe, path)

def translate_text(text: str, src_lang: str, tgt_lang: str = "fr"):
    tokenizer.src_lang = src_lang
    inputs = tokenizer(text, return_tensors="pt").to(device)
    tgt_id = tokenizer.get_lang_id(tgt_lang)

    with torch.no_grad():
        output = translator.generate(
            **inputs,
            forced_bos_token_id=tgt_id,
            max_length=128
        )

    return tokenizer.decode(output[0], skip_special_tokens=True)

# ================= MODE 3 — FILE SPEECH TO TEXT =================
@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    raw_path = f"raw_{uuid.uuid4()}"
    wav_path = f"{raw_path}.wav"

    try:
        with open(raw_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        convert_to_wav(raw_path, wav_path)
        result = await whisper_transcribe(wav_path)

        return {
            "text": result["text"],
            "language": result["language"]
        }

    finally:
        for p in [raw_path, wav_path]:
            if os.path.exists(p):
                os.remove(p)

# ================= MODE 1 — LIVE SUBTITLES =================
@app.websocket("/ws/subtitles")
async def subtitles_ws(ws: WebSocket):
    await ws.accept()

    audio_buffer = bytearray()

    try:
        while True:
            chunk = await ws.receive_bytes()
            audio_buffer.extend(chunk)

            # Transcribe every ~5 seconds
            if len(audio_buffer) < 16000 * 2 * 2:
                continue

            raw_path = f"raw_{uuid.uuid4()}"
            wav_path = f"{raw_path}.wav"

            try:
                with open(raw_path, "wb") as f:
                    f.write(audio_buffer)

                convert_to_wav(raw_path, wav_path)
                result = await whisper_transcribe(wav_path)

                text = result["text"]
                src_lang = result["language"]
                translated = translate_text(text, src_lang, "fr")

                await ws.send_json({
                    "original": text,
                    "translated": translated,
                    "language": src_lang
                })

                audio_buffer.clear()

            finally:
                for p in [raw_path, wav_path]:
                    if os.path.exists(p):
                        os.remove(p)

    except Exception:
        await ws.close()

# ================= MODE 2 — SPEECH TO SPEECH =================
@app.websocket("/ws/speech")
async def speech_ws(ws: WebSocket):
    await ws.accept()

    audio_buffer = bytearray()

    try:
        while True:
            chunk = await ws.receive_bytes()
            audio_buffer.extend(chunk)

            if len(audio_buffer) < 16000 * 2 * 5:
                continue

            raw_path = f"raw_{uuid.uuid4()}"
            wav_path = f"{raw_path}.wav"

            try:
                with open(raw_path, "wb") as f:
                    f.write(audio_buffer)

                convert_to_wav(raw_path, wav_path)
                result = await whisper_transcribe(wav_path)

                text = result["text"]
                src_lang = result["language"]
                translated = translate_text(text, src_lang, "fr")

                await ws.send_json({
                    "text": translated,
                    "language": src_lang
                })

                audio_buffer.clear()

            finally:
                for p in [raw_path, wav_path]:
                    if os.path.exists(p):
                        os.remove(p)

    except Exception:
        await ws.close()
