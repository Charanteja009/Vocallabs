# 🏛️ SAKSHI (साक्षी) — Hackathon Submission Documentation

> **Project Name**: Sakshi (साक्षी) — Safe, Auditable Multimodal Delivery-Evidence Reconciliation  
> **GitHub Repository**: [https://github.com/Charanteja009/Vocallabs.git](https://github.com/Charanteja009/Vocallabs.git)  
> **Live Demo URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
> **Track**: Multimodal / AI for Bharat / Agents & Automation  

---

## 📌 1. What We Built & How It Works

### The Problem
In India’s construction, infrastructure, and logistics sectors, site supervisors receive physical paper delivery receipts (challans) while site foremen send quick voice notes in spoken Hindi/Hinglish on WhatsApp. Material fraud and payment leakage occur when vendors deliver partial quantities (e.g. 50 cement bags instead of 100) or damaged goods while leaving paper receipts stating full quantities.

### The Solution: Sakshi (साक्षी)
**Sakshi** is an AI-powered, multimodal delivery reconciliation platform engineered specifically for Indian ground realities. Instead of allowing an LLM to blindly make financial payment approvals, Sakshi combines **Vision AI**, **Hindi/Hinglish Speech-to-Text (STT)**, a **Hindi Number Normalizer**, and a **Deterministic Financial Safety Engine** to verify physical receipts against site voice reports before money changes hands.

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
       │    • Groq Qwen Vision OCR (Receipt claims)                  │
       │    • Groq Whisper Turbo STT (Voice transcription)           │
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
       │    • Evidence Score (0-100) + Context-Aware "Ask Next"      │
       │    • Native Multilingual TTS Audio Review (6 Languages)     │
       │    • Immutable PostgreSQL Audit Trail (/media/ storage)     │
       └──────────────────────────────┬──────────────────────────────┘
```

---

## 🛠️ 2. Work Done & Individual Contributions

### Core Contributions
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

### Feature 1: Zero Financial Hallucination Guarantee
Generative AI models extract facts from raw images and audio, but **a deterministic Python rule engine (`app/safety.py`) makes the financial recommendation**. If evidence is missing, conflicting, or unreadable, the system strictly holds payment (`HOLD_FOR_REVIEW`).

### Feature 2: Hindi/Hinglish Number Normalizer & 1.0% Tolerance
Converts regional spoken words (*"athavan"* = 58, NOT 80!). For bill totals like ₹258,231.20 vs spoken ~₹258,000, the difference is ₹231.20 (0.09%). Since this is within the 1.0% configured tolerance policy, Sakshi issues `RECOMMEND_PROCEED` while preserving exact audit trails.

### Feature 3: 3-Tier Multi-Model Failover (Hackathon Rule Compliance)
Satisfies the mandatory *"Degrade Gracefully"* constraint (Page 2 of Hackathon Brief):
1. **Tier 1 (Cloud Primary)**: Groq Cloud API
2. **Tier 2 (Cloud Backup)**: OpenRouter Free Cloud API
3. **Tier 3 (Local Laptop Backup)**: Local Ollama Engine (`gpt-oss:120b-cloud`)

### Feature 4: Built-in 20-Case Automated Eval Harness
Includes a 20-case test suite (`eval/cases.json` & `/api/evaluate`) verifying 100% decision accuracy and 0 unsafe payment approvals.

---

## 📹 5. Demo Video Script & Submission Checklist

### Demo Video Recording Outline (2 to 3 Minutes)

1. **0:00 - 0:30 (Problem & Solution)**: Show physical paper receipt + WhatsApp voice note challenge at construction sites. Introduce Sakshi.
2. **0:30 - 1:00 (Demo Case 1 - Perfect Match & Tolerance)**:
   - Upload receipt `Challan-pdf-1-2048.webp`.
   - Enter transcript: `"Total bill do lakh athavan hazaar ke aas-paas hai."`
   - Show normalized amount `₹2,58,000`, 0.09% difference, and **`RECOMMEND_PROCEED`** banner.
3. **1:00 - 1:30 (Demo Case 2 - Material Shortage & Damage)**:
   - Enter transcript: `"10 cement bags rain me wet aur damaged ho gaye hain site par."`
   - Show **`HOLD_FOR_REVIEW`** verdict, `LOW (55/100)` quality score, condition conflict, and "Ask Next" photo request.
4. **1:30 - 2:00 (Multilingual Audio & Failover)**:
   - Click **"Listen to review"** and select **`Telugu (తెలుగు)`** or **`Hindi (हिन्दी)`** to demonstrate native MP3 audio playback.
   - Show terminal logs demonstrating 3-tier failover (`Groq ➔ OpenRouter ➔ Local Ollama`).
5. **2:00 - 2:30 (Eval Harness & Conclusion)**:
   - Run `.venv\Scripts\python.exe eval/test_amount_cases.py` in PowerShell showing **100% PASS** on all 20 cases.

---

### 📦 Submission Drive Folder Checklist
- [x] **GitHub Repository URL**: [https://github.com/Charanteja009/Vocallabs.git](https://github.com/Charanteja009/Vocallabs.git)
- [x] **Documentation File**: `SUBMISSION_DOCUMENTATION.md` & `README.md`
- [x] **Demo Video MP4**: 2-3 minute video recording following the script above
- [x] **Architecture Diagram & Screenshots**: Included in documentation
