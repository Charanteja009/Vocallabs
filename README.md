# 🏛️ SAKSHI (साक्षी) — Multimodal Delivery Evidence Reconciliation

> **Safe, Auditable Delivery-Evidence Reconciliation for Construction & Material Logistics**  
> *When the physical paper receipt and site voice note disagree, don't guess. AI extracts. A deterministic policy decides.*

---

## 📌 Submission Overview & Hackathon Compliance

| Requirement | Details / Link |
| :--- | :--- |
| **Project Name** | **Sakshi (साक्षी)** |
| **GitHub Repository** | [https://github.com/Charanteja009/Vocallabs.git](https://github.com/Charanteja009/Vocallabs.git) |
| **Live Demo URL** | [http://127.0.0.1:8000](http://127.0.0.1:8000) / Cloud Hosted |
| **Full Documentation** | [`SUBMISSION_DOCUMENTATION.md`](SUBMISSION_DOCUMENTATION.md) |
| **Hackathon Tracks** | **Multimodal** · **AI for Bharat** · **Agents & Automation** |
| **Decision Accuracy** | **100%** across 20-case test suite (`0` unsafe approvals) |

---

## 🚀 1. What We Built & How It Works

### The Problem
In India’s construction, infrastructure, and logistics sectors, site supervisors receive physical paper delivery receipts (challans) while site foremen send quick voice notes in spoken Hindi/Hinglish on WhatsApp. Material fraud and payment leakage occur when vendors deliver partial quantities (e.g. 50 cement bags instead of 100) or damaged goods while leaving paper receipts stating full quantities.

### The Solution
**Sakshi** is an AI-powered, multimodal delivery reconciliation platform engineered specifically for Indian ground realities. Instead of allowing an LLM to blindly make financial payment approvals, Sakshi combines **Vision AI**, **Hindi/Hinglish Speech-to-Text (STT)**, a **Hindi Number Normalizer**, and a **Deterministic Financial Safety Engine** to verify physical receipts against site voice reports before money changes hands.

---

## 🛠️ 2. Work Done & Individual Contributions

- **Multimodal AI Pipeline Integration**: Built async FastAPI endpoints orchestrating Groq Qwen Vision (`qwen3.6-27b`) for document claim extraction and Groq Whisper (`whisper-large-v3-turbo`) for Hindi/Hinglish speech transcription.
- **Hindi Spoken Number Normalizer (`app/hindi_normalizer.py`)**: Designed regex and dictionary parser to convert complex Indian spoken number phrases (e.g. *"do lakh athavan hazaar"*) into numeric values (`258000`) and precision tags (`approximate` vs `exact`).
- **Deterministic Safety Policy Engine (`app/safety.py`)**: Implemented non-negotiable financial guardrails enforcing zero-hallucination payment holds (`HOLD_FOR_REVIEW`), 1.0% tolerance calculation, and evidence quality scoring (0-100).
- **3-Tier Multi-Model Failover System (`app/main.py`)**: Built automatic failover architecture across **Groq Cloud API** ➔ **OpenRouter Free API** ➔ **Local Ollama Engine (`gpt-oss:120b-cloud`)**, satisfying the hackathon's mandatory *"Degrade Gracefully"* rule.
- **Native Regional Language TTS Proxy (`/api/tts`)**: Created backend audio streaming proxy delivering native MP3 audio in Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, and English.
- **User Auth & Full-Screen SPA (`app/static/`)**: Developed single-page web app with JWT (HS256) bearer authentication, bcrypt password hashing, login/signup routes, and history management.

---

## 👥 3. Team Roles & Responsibilities

| Team Member | Role | Key Contributions |
| :--- | :--- | :--- |
| **Team Member 1 (Lead)** | **Full-Stack AI & Safety Architect** | Groq Multimodal AI integration, Deterministic Safety Engine (`app/safety.py`), Hindi Number Normalizer (`app/hindi_normalizer.py`), and 3-Tier Failover System. |
| **Team Member 2** | **Backend & Database Engineer** | FastAPI API Gateway, PostgreSQL ORM schemas, JWT authentication, `/media/` file persistence, and Docker Compose orchestration. |
| **Team Member 3** | **Frontend & UI/UX Developer** | SPA dashboard interface, real-time verdict banners, multilingual audio review controls, history card rendering, and CSS styling. |
| **Team Member 4** | **Evaluation & QA Engineer** | 20-case test suite (`eval/cases.json`), 5 amount normalization tests (`eval/test_amount_cases.py`), failure logging, and demo video preparation. |

---

## 💡 4. Key Features & Technical Decisions

1. **Zero Financial Hallucination Guarantee**: Generative AI extracts facts, but a **deterministic Python rule engine (`app/safety.py`)** makes the payment decision.
2. **Hindi/Hinglish Number Normalizer & 1.0% Tolerance**: Normalizes words (*"athavan"* = 58, NOT 80!). Evaluates bill totals within a 1.0% configured tolerance policy.
3. **3-Tier Multi-Model Failover**: Satisfies the mandatory *"Degrade Gracefully"* rule (Groq Cloud ➔ OpenRouter Free Cloud ➔ Local Ollama).
4. **Built-in 20-Case Automated Eval Harness**: Includes `eval/cases.json` and `/api/evaluate` endpoint verifying **100% accuracy**.

---

## ⚡ Quick Start / Run Locally

### Requirements
- Python 3.11+
- Groq API Key

```bash
# 1. Install dependencies
.venv\Scripts\pip.exe install -r requirements.txt

# 2. Set API Key in .env
GROQ_API_KEY=gsk_your_key_here

# 3. Run FastAPI server
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 🧪 Run Evaluation Harness

```powershell
.venv\Scripts\python.exe eval/test_amount_cases.py
```
> Outputs **`ALL 5 NEW AMOUNT TESTS & EVAL CASES PASSED 100%!`**
