

# 🌍 InstantTranslate AI – Real-Time Voice & Text TranslatoR

InstantTranslate AI is a real-time multilingual translation system that supports both **text-based** and **voice-based** translation using **open-source AI models**.  

This is a a real-time multilingual voice translator using FastAPI, WebSockets, Whisper for speech recognition, and Facebook M2M100 for neural translation. The 
system supports streaming audio, automatic language detection, and scalable multilingual expansion.

The project is fully **offline-capable**, **free**, and designed for **final-year engineering projects, research, and resume portfolios**.


---

## 🚀 Features

- 🎤 **Real-Time Voice Translation**
  - Speech → Text → Translated Text
- ⌨️ **Text-to-Text Translation**
- 🌍 **Multilingual Support**
  - English
  - Hindi
  - Telugu
  - Tamil
  - Spanish
  - German
- 🧠 **Rule-Based Grammar Polishing**
  - Improves translation quality for Indian languages
- ⚡ **Low-Latency WebSocket Streaming**
- 🖥️ **Modern Web Interface**
- 💯 **100% Free & Open Source (No APIs, No Keys)**

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

Low-resource languages like Telugu and Tamil often receive **incomplete or literal translations** from neural models.
## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/ai-linguaflow.git
cd ai-linguaflow
2️⃣ Create Virtual Environment
bash
Copy code
python -m venv venv
venv\Scripts\activate   # Windows
3️⃣ Install Dependencies
bash
Copy code
pip install fastapi uvicorn torch numpy whisper transformers anyio
⚠️ First run will download Whisper and NLLB models (may take time).

▶️ Running the Application
bash
Copy code
uvicorn backend.main:app --host 0.0.0.0 --port 8080
Open in browser:

arduino
Copy code
http://localhost:8080
🎤 How Voice Translation Works
User clicks Start Listening

Microphone audio is streamed using WebSocket

Whisper converts speech to text

NLLB-200 translates the text

Grammar polishing improves sentence quality

Translated text is displayed in real time



AI LinguaFlow includes a **rule-based grammar polishing layer** that:
- Fixes incomplete sentence endings
- Corrects common verb phrase errors
- Improves fluency and readability

