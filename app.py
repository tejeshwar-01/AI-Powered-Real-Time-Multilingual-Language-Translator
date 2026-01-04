import os, uuid, shutil, torch, whisper, asyncio
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
print("🚀 Device:", device)

# ================= MODELS =================
whisper_model = whisper.load_model("base", device=device)

MODEL_NAME = "facebook/m2m100_418M"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
translator = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)

# ================= FRONTEND =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# ================= HELPERS =================
def detect_lang(text):
    return "hi" if any(c in text for c in "अआइईउऊ") else "en"

def translate_text(text, tgt):
    tokenizer.src_lang = detect_lang(text)
    inputs = tokenizer(text, return_tensors="pt").to(device)
    tgt_id = tokenizer.get_lang_id(tgt)
    with torch.no_grad():
        out = translator.generate(**inputs, forced_bos_token_id=tgt_id)
    return tokenizer.decode(out[0], skip_special_tokens=True)

# ================= MODE 3 — MIC FIX =================
@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    path = f"tmp_{uuid.uuid4()}.wav"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    result = whisper_model.transcribe(path)
    os.remove(path)
    return {"text": result["text"]}

# ================= MODE 1 — LIVE SUBTITLES =================
@app.websocket("/ws/subtitles")
async def subtitles_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_bytes()
            path = f"chunk_{uuid.uuid4()}.wav"
            with open(path, "wb") as f:
                f.write(data)

            text = whisper_model.transcribe(path)["text"]
            translated = translate_text(text, "fr")

            await ws.send_json({
                "original": text,
                "translated": translated
            })
            os.remove(path)
    except:
        await ws.close()

# ================= MODE 2 — FULL SPEECH-TO-SPEECH =================
@app.websocket("/ws/speech")
async def speech_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_bytes()
            path = f"audio_{uuid.uuid4()}.wav"
            with open(path, "wb") as f:
                f.write(data)

            text = whisper_model.transcribe(path)["text"]
            translated = translate_text(text, "fr")

            await ws.send_json({
                "text": translated
            })
            os.remove(path)
    except:
        await ws.close()
