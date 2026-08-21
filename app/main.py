"""Sakshi: safe, auditable multimodal delivery-evidence reconciliation."""
import base64
import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from urllib import error, request

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pydantic import BaseModel

from app.safety import pending_review, safe_result

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "static"
EVAL_CASES = ROOT / "eval" / "cases.json"
load_dotenv(ROOT / ".env")
MAX_BYTES = 12 * 1024 * 1024
GROQ_BASE = "https://api.groq.com/openai/v1"
GROQ_VISION_MODEL = "qwen/qwen3.6-27b"
app = FastAPI(title="Sakshi")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class ReviewPacket(BaseModel):
    id: str
    document: dict
    transcript: str
    result: dict
    observability: dict | None = None


def groq_json(url: str, payload: dict) -> dict:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise HTTPException(503, "GROQ_API_KEY is missing")
    req = request.Request(url, data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Sakshi-Hackathon/2.0"}, method="POST")
    try:
        with request.urlopen(req, timeout=50) as response:
            return json.loads(response.read())
    except error.HTTPError as exc:
        raise HTTPException(502, f"Model request failed: {exc.read().decode(errors='replace')[:300]}") from exc
    except error.URLError as exc:
        raise HTTPException(503, f"Model network unavailable: {exc.reason}") from exc


def content(response: dict) -> str:
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(502, "Model returned an unreadable response.") from exc


def parse_json(raw: str) -> dict:
    try:
        return json.loads(raw.removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError as exc:
        raise HTTPException(502, "Model did not return valid structured evidence.") from exc


async def transcribe(audio: UploadFile) -> str:
    binary = await audio.read()
    if not binary or len(binary) > MAX_BYTES:
        raise HTTPException(400, "Audio must be between 1 byte and 12 MB.")
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise HTTPException(503, "GROQ_API_KEY is missing")
    try:
        reply = Groq(api_key=key).audio.transcriptions.create(file=(audio.filename or "voice-note.wav", binary), model="whisper-large-v3-turbo", response_format="json", temperature=0.0)
        return reply.text.strip()
    except Exception as exc:
        raise HTTPException(503, "Audio transcription unavailable") from exc


async def image_to_claim(image: UploadFile) -> dict:
    binary = await image.read()
    if not binary or len(binary) > MAX_BYTES:
        raise HTTPException(400, "Image must be between 1 byte and 12 MB.")
    mime = image.content_type or mimetypes.guess_type(image.filename or "")[0] or "image/jpeg"
    prompt = """Extract only visible delivery-challan evidence. Return JSON only:
{"supplier":{"value":string|null,"confidence":0-1},"date":{"value":string|null,"confidence":0-1},"items":[{"name":string,"quantity":number|null,"unit":string|null,"condition":string|null,"confidence":0-1}],"amount":{"value":number|null,"currency":string|null,"confidence":0-1},"unknowns":[string]}. Never infer invisible values."""
    response = groq_json(f"{GROQ_BASE}/chat/completions", {"model": GROQ_VISION_MODEL, "temperature": 0.01, "reasoning_effort": "none", "max_completion_tokens": 1024, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(binary).decode()}", "detail": "high"}}]}]})
    return parse_json(content(response))


def assess_claims(claim: dict, transcript: str) -> dict:
    prompt = f"""Compare two independent delivery evidence sources. Return JSON only:
{{"conflicts":[{{"field":string,"document_claim":string,"voice_claim":string,"why":string}}],"agreements":[string],"missing_information":[string]}}
Document evidence: {json.dumps(claim)}
Foreman Hindi/Hinglish transcript: {transcript!r}
Only report stated evidence. Identify quantity, material, condition, supplier, amount and date conflicts. Do not make a payment decision."""
    response = groq_json(f"{GROQ_BASE}/chat/completions", {"model": GROQ_VISION_MODEL, "temperature": 0.01, "reasoning_effort": "none", "max_completion_tokens": 1024, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]})
    return parse_json(content(response))


def empty_document() -> dict:
    return {"supplier": {"value": None, "confidence": 0}, "date": {"value": None, "confidence": 0}, "items": [], "amount": {"value": None, "currency": None, "confidence": 0}, "unknowns": ["Document analysis unavailable"]}


def response_with_pending(reason: str, transcript: str, document: dict | None, timings: dict, started: float) -> dict:
    document = document or empty_document()
    return {"id": str(uuid.uuid4())[:8], "document": document, "transcript": transcript, "result": pending_review(reason, document, transcript), "observability": {"timings_ms": timings, "total_ms": round((time.perf_counter() - started) * 1000)}}


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "groq_key_configured": bool(os.getenv("GROQ_API_KEY")), "safety_policy": "deterministic"}


@app.get("/api/evaluate")
def evaluate():
    cases = json.loads(EVAL_CASES.read_text(encoding="utf-8"))
    runs, unsafe = [], 0
    for case in cases:
        actual = safe_result(case["document"], case["transcript"], case["assessment"])["decision"]
        passed = actual == case["expected_decision"]
        unsafe += int(actual == "RECOMMEND_PROCEED" and case["expected_decision"] != "RECOMMEND_PROCEED")
        runs.append({"id": case["id"], "name": case["name"], "expected": case["expected_decision"], "actual": actual, "passed": passed})
    passed = sum(run["passed"] for run in runs)
    return {"case_count": len(cases), "passed": passed, "decision_accuracy": round(passed / len(cases) * 100, 1), "unsafe_approvals": unsafe, "runs": runs}


@app.post("/api/review-packet")
def review_packet(packet: ReviewPacket):
    body = {"packet_version": "1.0", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **packet.model_dump()}
    return JSONResponse(body, headers={"Content-Disposition": f'attachment; filename="sakshi-review-{packet.id}.json"'})


@app.post("/api/reconcile")
async def reconcile(image: UploadFile = File(...), transcript: str = Form(""), audio: UploadFile | None = File(None)):
    started, timings = time.perf_counter(), {}
    transcript = transcript.strip()
    if not transcript and audio:
        phase = time.perf_counter()
        try:
            transcript = await transcribe(audio)
            timings["transcription_ms"] = round((time.perf_counter() - phase) * 1000)
        except HTTPException as exc:
            return response_with_pending(exc.detail, transcript, None, timings, started)
    if len(transcript) < 8:
        raise HTTPException(400, "Upload a voice note or add a short transcript; Sakshi will not guess what was said.")
    phase = time.perf_counter()
    try:
        document = await image_to_claim(image)
        timings["vision_ms"] = round((time.perf_counter() - phase) * 1000)
    except HTTPException as exc:
        return response_with_pending(exc.detail, transcript, None, timings, started)
    phase = time.perf_counter()
    try:
        result = safe_result(document, transcript, assess_claims(document, transcript))
        timings["reconciliation_ms"] = round((time.perf_counter() - phase) * 1000)
    except HTTPException as exc:
        return response_with_pending(exc.detail, transcript, document, timings, started)
    return {"id": str(uuid.uuid4())[:8], "document": document, "transcript": transcript, "result": result, "observability": {"timings_ms": timings, "total_ms": round((time.perf_counter() - started) * 1000), "estimated_model_cost_usd": "Demo estimate: confirm against current provider pricing before production"}}
