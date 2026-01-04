# 🌍 InstantTranslate AI – Real-Time Voice & Text Translator

InstantTranslate AI is a real-time multilingual translation system that supports both **text-based** and **voice-based** translation using **open-source AI models**.

It is built using **FastAPI**, **WebSockets**, **Whisper** for speech recognition, and **NLLB-200 (Meta AI)** for neural machine translation.  
The system supports **streaming audio**, **automatic speech recognition**, and **scalable multilingual translation**.

This project is fully **offline-capable**, **free**, and designed for **final-year engineering projects, research, and resume portfolios**.

---

## 🚀 Features

- 🎤 **Real-Time Voice Translation**
  - Speech → Text → Translated Text
- ⌨️ **Text-to-Text Translation**
- 🌍 **Multilingual Support**
  - Hindi
  - Telugu
  - Tamil
  - Spanish
  - German
- 🧠 **Rule-Based Grammar Polishing**
  - Improves translation quality for Indian languages
- ⚡ **Low-Latency WebSocket Streaming**
- 🖥️ **Modern Web Interface**
- 💯 **100% Free & Open Source**
  - No APIs
  - No API keys
  - Fully offline after model download

---

## 🧠 System Architecture


User (Voice / Text)
↓
Frontend (Web UI)
↓
WebSocket (FastAPI)
↓
Whisper (Speech-to-Text)
↓
NLLB-200 (Translation)
↓
Grammar Polishing Layer
↓
Translated Text Output

---

## 🛠️ Technologies Used

### Backend
- Python
- FastAPI
- WebSockets
- Whisper (OpenAI)
- NLLB-200 (Meta AI)
- PyTorch
- NumPy

### Frontend
- HTML
- CSS (Glassmorphism UI)
- JavaScript
- Web Audio API

---

## 🌐 Supported Languages

| Language | Code |
|--------|------|
| Hindi | hi |
| Telugu | te |
| Tamil | ta |
| Spanish | es |
| German | de |

---

## ✨ Grammar Polishing (Rule-Based)

Low-resource languages like **Telugu** and **Tamil** often receive incomplete or literal translations from neural machine translation models.

To address this, InstantTranslate AI includes a **rule-based grammar polishing layer** that:

- Fixes incomplete sentence endings  
- Corrects common verb phrase errors  
- Improves fluency and readability  


---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/instanttranslate-ai.git
cd instanttranslate-ai
## ⚙️ Create Virtual Environment

``bash
python -m venv venv
venv\Scripts\activate   # Windows

## Install dependencies
pip install fastapi uvicorn torch numpy whisper transformers anyio
⚠️ First run will download Whisper and NLLB-200 models.
This may take some time depending on your internet speed.

Running the Application
uvicorn backend.main:app --host 0.0.0.0 --port 8080

🌐 Open in Browser
http://localhost:8080


