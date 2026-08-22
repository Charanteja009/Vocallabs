# 🏛️ SAKSHI (साक्षी) — Project Technical Documentation

> **Project Title**: Sakshi (साक्षी) — Safe, Auditable Multimodal Delivery-Evidence Reconciliation System  
> **🌐 Live Production URL**: [https://vocallabs-zhjk.onrender.com/](https://vocallabs-zhjk.onrender.com/)  
> **🐙 GitHub Repository**: [https://github.com/Charanteja009/Vocallabs](https://github.com/Charanteja009/Vocallabs)  
> **Backend Framework**: FastAPI (Python 3.11) | Uvicorn ASGI Server  
> **Database Engine**: PostgreSQL 15 / SQLAlchemy ORM  

---

## 🌐 Project Links & Quick Access

- **Live Production App**: [https://vocallabs-zhjk.onrender.com/](https://vocallabs-zhjk.onrender.com/)
- **Source Code Repository**: [https://github.com/Charanteja009/Vocallabs](https://github.com/Charanteja009/Vocallabs)
- **Automated 20-Case Evaluation API**: [https://vocallabs-zhjk.onrender.com/api/evaluate](https://vocallabs-zhjk.onrender.com/api/evaluate)

---

## 📌 1. Project Overview & Problem Context

### The Industry Problem
In India’s construction, infrastructure, and material logistics sectors, site supervisors receive physical paper delivery receipts (challans) while site foremen record quick voice reports in spoken Hindi/Hinglish on WhatsApp. Material fraud and financial payment leakage occur when vendors deliver partial quantities (e.g. 50 cement bags instead of 100) or damaged goods while leaving paper receipts stating full quantities.

### The Solution: Sakshi (साक्षी)
**Sakshi (साक्षी)** is an AI-powered, multimodal delivery reconciliation platform engineered for industrial supply chains. Instead of allowing generative AI to blindly make financial payment approvals, Sakshi combines **Vision AI**, **Hindi/Hinglish Speech-to-Text (STT)**, a **Hindi Spoken Number Normalizer**, and a **Deterministic Financial Safety Engine** to verify physical receipts against site voice reports before money changes hands.

---

## 🏗️ 2. System Architecture & Workflow

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

## 🛠️ 3. Core Component Deep Dive

### A. Pre-Reconciliation Hindi Spoken Number Normalizer (`app/hindi_normalizer.py`)
- **Purpose**: Converts regional spoken Indian number words into structured numeric data before reconciliation.
- **Key Examples**:
  - `"do lakh athavan hazaar"` ➔ `258000` (ensures `"athavan"` = 58, not 80!).
  - `"do lakh athavan hazaar do sau ikattis"` ➔ `258231`.
  - `"pachaas hazaar"` ➔ `50000`.
- **Precision Detection**: Detects approximation keywords (`lagbhag`, `aas-paas`, `around`, `approximately`, `करीब`, `लगभग`) and sets `"precision": "approximate"` or `"precision": "exact"`.

### B. Deterministic Financial Safety Policy Engine (`app/safety.py`)
- **Zero Hallucination Guarantee**: Generative AI models extract facts from raw images and speech, but a **deterministic Python rule engine** makes the financial recommendation.
- **Configurable Tolerance**: `APPROX_AMOUNT_TOLERANCE_PERCENT = 1.0` (1.0%).
- **4 Amount Reconciliation States**:
  1. `MATCH`: Exact numeric match or difference <= 0.05%.
  2. `MATCH_WITHIN_TOLERANCE`: Approximate voice amount with difference <= 1.0% policy limit (issues `RECOMMEND_PROCEED`).
  3. `CONFLICT`: Difference > 1.0% or exact mismatch (issues `HOLD_FOR_REVIEW`).
  4. `UNVERIFIED`: Amount missing or unstated.

### C. 3-Tier Multi-Model Failover Architecture (`app/main.py`)
- **Tier 1 (Cloud Primary)**: Groq Cloud API (`qwen/qwen3.6-27b` Vision + `whisper-large-v3-turbo` STT).
- **Tier 2 (Cloud Backup)**: OpenRouter Free Cloud API (`openrouter/auto`).
- **Tier 3 (Local Laptop Fallback)**: Local Ollama Engine (`gpt-oss:120b-cloud` at `http://localhost:11434`).

### D. Native Regional Language Voice Synthesis (`/api/tts`)
FastAPI audio proxy route (`/api/tts`) streaming native MP3 audio to bypass browser CORS restrictions. Supports native audio playback for:
- Telugu (`తెలుగు`)
- Hindi (`हिन्दी`)
- Tamil (`தமிழ்`)
- Kannada (`ಕನ್ನಡ`)
- Malayalam (`മലയാളം`)
- Marathi (`मराठी`)
- English

### E. User Authentication & PostgreSQL Persistence
- **JWT (HS256) & bcrypt**: Token-based authentication with salted password hashing.
- **Database & Media Storage**: PostgreSQL integration with automatic media saving for uploaded receipts and audio notes (`/media/`).

---

## 🧪 4. Evaluation Harness & Verification

- **20-Case Automated Test Suite**: Located at `eval/cases.json` and accessible via `GET /api/evaluate`. Achieves **100% decision accuracy** and **zero unsafe payment approvals**.
- **5-Case Amount Normalization Suite**: Tested via `eval/test_amount_cases.py`, verifying 100% pass rate across exact, approximate, shortage, damage, and unverified amount scenarios.

---

## 📊 5. Complete Technical Stack Summary

| Layer | Component | Technology Used |
| :--- | :--- | :--- |
| **Live App URL** | Production Cloud | [https://vocallabs-zhjk.onrender.com/](https://vocallabs-zhjk.onrender.com/) |
| **Repository** | Source Code | [https://github.com/Charanteja009/Vocallabs](https://github.com/Charanteja009/Vocallabs) |
| **Vision AI** | Receipt OCR | Groq Qwen Vision (`qwen/qwen3.6-27b`) |
| **Speech AI** | Transcription | Groq Whisper (`whisper-large-v3-turbo`) |
| **Safety Engine** | Guardrails | Python Deterministic Rule Engine (`app/safety.py`) |
| **Normalizer** | Hindi Numbers | Python Custom Normalizer (`app/hindi_normalizer.py`) |
| **Backend** | API Gateway | FastAPI, Python 3.11, Uvicorn |
| **Database** | Storage | PostgreSQL 15, SQLAlchemy ORM |
| **Security** | Authentication | JWT (HS256) Bearer Tokens, bcrypt Hashing |
| **Frontend** | Single Page App | HTML5, CSS3, Vanilla ES6 JavaScript |
