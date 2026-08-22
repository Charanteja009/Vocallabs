# 🏛️ SAKSHI (साक्षी) — Project Technical Documentation

> **Project Name**: Sakshi (साक्षी) — Safe, Auditable Multimodal Delivery-Evidence Reconciliation  
> **🌐 Live Production URL**: [https://vocallabs-zhjk.onrender.com/](https://vocallabs-zhjk.onrender.com/)  
> **🐙 GitHub Repository**: [https://github.com/Charanteja009/Vocallabs](https://github.com/Charanteja009/Vocallabs)  
> **Backend Engine**: FastAPI (Python 3.11) | Uvicorn ASGI Server  
> **Database Engine**: PostgreSQL 15 | SQLAlchemy ORM  

---

## 🌐 Quick Access Links

- **Live App URL**: [https://vocallabs-zhjk.onrender.com/](https://vocallabs-zhjk.onrender.com/)
- **GitHub Repository**: [https://github.com/Charanteja009/Vocallabs](https://github.com/Charanteja009/Vocallabs)
- **20-Case Eval Endpoint**: [https://vocallabs-zhjk.onrender.com/api/evaluate](https://vocallabs-zhjk.onrender.com/api/evaluate)

---

## 📌 1. Project Overview & Operational Workflow

### The Problem
In construction, infrastructure, and logistics operations across India, site supervisors receive physical paper delivery receipts (challans) while site foremen record quick voice notes in spoken Hindi/Hinglish on WhatsApp. Material fraud and payment leakage occur when vendors deliver partial quantities (e.g. 50 cement bags instead of 100) or damaged goods while leaving physical receipts stating full quantities.

### The Solution
**Sakshi (साक्षी)** is an AI-powered, multimodal delivery reconciliation platform engineered for industrial supply chains. Instead of allowing generative AI to blindly make financial payment approvals, Sakshi combines **Vision AI**, **Hindi/Hinglish Speech-to-Text (STT)**, a **Hindi Spoken Number Normalizer**, and a **Deterministic Financial Safety Engine** to verify physical receipts against site voice reports before money changes hands.

```
       ┌─────────────────────────────────────────────────────────────┐
       │                   Physical Paper Receipt                    │
       │                         +                                   │
       │               Site Foreman Voice Note (Hinglish)            │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │ 1. Multimodal AI Extraction                                 │
       │    • Groq Qwen Vision OCR (Receipt claim extraction)        │
       │    • Groq Whisper Turbo STT (Voice note transcription)      │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │ 2. Pre-Reconciliation Hindi Number Normalizer               │
       │    • "do lakh athavan hazaar" ➔ ₹2,58,000 (approximate)      │
       │    • Precision & original phrase preservation               │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │ 3. Deterministic Safety Policy & Tolerance Engine            │
       │    • 1.0% Policy Tolerance Check                            │
       │    • 4 Amount States (MATCH, TOLERANCE, CONFLICT, UNVERIFIED)│
       │    • Material Shortage & Condition Conflict Detection       │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │ 4. Output & Audit Trail                                     │
       │    • Decision: RECOMMEND_PROCEED / HOLD_FOR_REVIEW          │
       │    • Evidence Score (0-100) + Actionable Guidance           │
       │    • Native Multilingual TTS Audio Review (6 Languages)     │
       │    • Immutable PostgreSQL Audit Trail (/media/ storage)     │
       └──────────────────────────────┬──────────────────────────────┘
```

---

## 🏗️ 2. Technical Architecture & Component Breakdown

Sakshi is built as a **Cloud-Native Microservices Architecture** (also deployable as a high-performance unified service):

### A. Frontend Single Page Application (`app/static/`)
- **Technology**: Vanilla HTML5, CSS3, ES6 JavaScript.
- **Authentication**: JWT (HS256) bearer token management with `localStorage` persistence.
- **Components**: Dedicated full-screen Login, Signup, and Dashboard tab views (`Compare Evidence`, `Audit History`, `Evaluation Harness`).

### B. API Gateway & Backend Engine (`app/main.py`)
- **Technology**: FastAPI (Python 3.11), Uvicorn ASGI server.
- **Endpoints**:
  - `POST /api/auth/register` & `POST /api/auth/login` (Authentication)
  - `POST /api/reconcile` (Multimodal evidence reconciliation)
  - `GET /api/tts` (Native regional text-to-speech audio streaming)
  - `GET /api/history/list` & `DELETE /api/history/delete/{id}` (Audit trail management)
  - `GET /api/evaluate` (20-case automated test suite execution)

### C. Multimodal AI Extraction Layer
- **Speech-to-Text (STT)**: **Groq Whisper (`whisper-large-v3-turbo`)** for fast transcription of code-mixed Hindi, Hinglish, and Indian English speech.
- **Vision OCR**: **Groq Qwen Vision (`qwen/qwen3.6-27b`)** for document reading of printed and handwritten Indian challans, Mathadi vouchers, and transport slips.
- **Payload Optimization**: Automatic image resizing (`optimize_image_bytes`) using Pillow to compress camera uploads to max 1600x1600 resolution and JPEG quality 85, keeping base64 payloads under 500KB.

### D. Hindi Spoken Number Normalizer (`app/hindi_normalizer.py`)
- **Algorithm**: Regex-based dictionary parser converting Indian spoken number phrases into structured numeric data.
- **Examples**:
  - `"do lakh athavan hazaar"` ➔ `258000` (ensures `"athavan"` = 58, not 80).
  - `"do lakh athavan hazaar do sau ikattis"` ➔ `258231`.
  - `"pachaas hazaar"` ➔ `50000`.
- **Precision Detection**: Detects approximation keywords (`lagbhag`, `aas-paas`, `around`, `approximately`, `करीब`, `लगभग`) to set `"precision": "approximate"` or `"precision": "exact"`.

### E. Financial Safety Policy Engine (`app/safety.py`)
- **Tolerance Policy**: Configurable constant `APPROX_AMOUNT_TOLERANCE_PERCENT = 1.0` (1.0%).
- **4-State Amount Reconciliation**:
  1. `MATCH`: Exact numeric match or difference <= 0.05%.
  2. `MATCH_WITHIN_TOLERANCE`: Approximate voice amount with difference <= 1.0% policy limit (issues `RECOMMEND_PROCEED`).
  3. `CONFLICT`: Difference > 1.0% or exact mismatch (issues `HOLD_FOR_REVIEW`).
  4. `UNVERIFIED`: Amount missing or unstated.
- **Evidence Quality Score**: Calculates a transparent 0-100 score based on item readability, quantity presence, transcript length, and evidence conflicts.

### F. 3-Tier Multi-Model Failover System
- **Tier 1 (Cloud Primary)**: Groq Cloud API (`qwen3.6-27b` + `whisper-large-v3-turbo`).
- **Tier 2 (Cloud Secondary)**: OpenRouter Free Cloud API (`openrouter/auto`).
- **Tier 3 (Local Laptop Fallback)**: Local Ollama Engine (`gpt-oss:120b-cloud` / `http://localhost:11434`).

### G. Database & File Persistence
- **Database**: SQLite for local development (`sakshi.db`), PostgreSQL 15 for production Docker Compose / Cloud deployment.
- **Media Storage**: `/media/` directory storing uploaded receipt images (`.jpg`, `.webp`) and recorded audio files (`.wav`).

---

## 💡 3. Key Features & Engineering Decisions

### Feature 1: Zero Financial Hallucination Guarantee
Generative AI models extract facts from raw images and speech, but a **deterministic Python rule engine (`app/safety.py`)** makes the financial recommendation. If evidence is missing, conflicting, or unreadable, the system strictly holds payment (`HOLD_FOR_REVIEW`).

### Feature 2: Native Regional Multilingual Voice Synthesis
Added `/api/tts` proxy route to stream clean MP3 audio directly from native voice engines, bypassing browser CORS restrictions. Supports native audio playback for:
- Telugu (`తెలుగు`)
- Hindi (`हिन्दी`)
- Tamil (`தமிழ்`)
- Kannada (`ಕನ್ನಡ`)
- Malayalam (`മലയാളം`)
- Marathi (`मराठी`)
- English

### Feature 3: Automated 20-Case Evaluation Harness
Includes a 20-case test suite (`eval/cases.json` & `eval/test_amount_cases.py`) verifying 100% decision accuracy and 0 unsafe payment approvals.

---

## 👥 4. Team Member Roles & Contributions

| Team Member | Role | Key Contributions |
| :--- | :--- | :--- |
| **Team Member 1 (Lead)** | **Full-Stack AI & Safety Architect** | Groq Multimodal AI integration, Deterministic Safety Engine (`app/safety.py`), Hindi Number Normalizer (`app/hindi_normalizer.py`), and 3-Tier Failover System. |
| **Team Member 2** | **Backend & Database Engineer** | FastAPI API Gateway, PostgreSQL ORM schemas, JWT authentication, `/media/` file persistence, and Docker Compose orchestration. |
| **Team Member 3** | **Frontend & UI/UX Developer** | SPA dashboard interface, real-time verdict banners, multilingual audio review controls, history card rendering, and CSS styling. |
| **Team Member 4** | **Evaluation & QA Engineer** | 20-case test suite (`eval/cases.json`), 5 amount normalization tests (`eval/test_amount_cases.py`), and system verification. |
