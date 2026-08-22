"""Deterministic safety policy for Sakshi evidence reconciliation."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from app.hindi_normalizer import normalize_hindi_numbers

# Configurable tolerance for approximate voice amount claims (1.0 = 1%)
APPROX_AMOUNT_TOLERANCE_PERCENT = 1.0


def clean_text(value: Any) -> str:
    """Return a lowercase, whitespace-normalized comparison value."""
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def confidence_label(value: Any) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "LOW"
    if score >= 0.85:
        return "HIGH"
    if score >= 0.70:
        return "MEDIUM"
    return "LOW"


def evaluate_amount_reconciliation(doc_amount_record: Optional[dict], voice_claim: dict) -> dict:
    """
    Evaluates amount alignment between document and voice claim into 4 distinct states:
    1. MATCH
    2. MATCH_WITHIN_TOLERANCE
    3. CONFLICT
    4. UNVERIFIED
    """
    doc_val = doc_amount_record.get("value") if isinstance(doc_amount_record, dict) else None
    voice_val = voice_claim.get("value")
    precision = voice_claim.get("precision", "exact")
    orig_text = voice_claim.get("original_text", "")

    if doc_val is None or voice_val is None:
        return {
            "status": "UNVERIFIED",
            "document_amount": doc_val,
            "voice_amount": voice_val,
            "precision": precision,
            "original_phrase": orig_text,
            "difference": None,
            "difference_percent": None
        }

    try:
        doc_float = float(doc_val)
        voice_float = float(voice_val)
    except (ValueError, TypeError):
        return {
            "status": "UNVERIFIED",
            "document_amount": doc_val,
            "voice_amount": voice_val,
            "precision": precision,
            "original_phrase": orig_text,
            "difference": None,
            "difference_percent": None
        }

    diff = abs(doc_float - voice_float)
    diff_percent = (diff / doc_float * 100.0) if doc_float > 0 else 0.0

    if diff == 0 or diff_percent <= 0.05:
        status = "MATCH"
    elif precision == "approximate":
        if diff_percent <= APPROX_AMOUNT_TOLERANCE_PERCENT:
            status = "MATCH_WITHIN_TOLERANCE"
        else:
            status = "CONFLICT"
    else:
        status = "CONFLICT"

    return {
        "status": status,
        "document_amount": doc_float,
        "voice_amount": voice_float,
        "precision": precision,
        "original_phrase": orig_text,
        "difference": round(diff, 2),
        "difference_percent": round(diff_percent, 2)
    }


def evidence_score(document: dict, transcript: str, conflicts: list[dict]) -> dict:
    """A transparent evidence-quality score, never a model probability."""
    factors: list[dict] = []
    score = 100
    items = document.get("items") or []
    if not items:
        score -= 35
        factors.append({"factor": "No readable delivery item", "impact": -35})
    for item in items:
        if item.get("quantity") is None:
            score -= 20
            factors.append({"factor": f"Missing quantity for {item.get('name') or 'item'}", "impact": -20})
        conf = item.get("confidence")
        conf_val = float(conf) if conf is not None else 0.95
        if conf_val < 0.70:
            score -= 15
            factors.append({"factor": f"Low readability for {item.get('name') or 'item'}", "impact": -15})
    if len(transcript.strip()) < 16:
        score -= 25
        factors.append({"factor": "Voice evidence is too short or ambiguous", "impact": -25})
    if conflicts:
        penalty = min(45, 15 * len(conflicts))
        score -= penalty
        factors.append({"factor": "Independent evidence conflicts", "impact": -penalty})
    score = max(0, score)
    return {"score": score, "level": "HIGH" if score >= 85 else "MEDIUM" if score >= 70 else "LOW", "factors": factors}


def document_provenance(document: dict) -> list[dict]:
    evidence: list[dict] = []
    for field in ("supplier", "date"):
        record = document.get(field) or {}
        if record.get("value") is not None:
            evidence.append({"field": field, "value": record["value"], "source": "delivery_challan", "quality": confidence_label(record.get("confidence"))})
    amount = document.get("amount") or {}
    if amount.get("value") is not None:
        evidence.append({"field": "amount", "value": f"{amount['value']} {amount.get('currency') or ''}".strip(), "source": "delivery_challan", "quality": confidence_label(amount.get("confidence"))})
    for item in document.get("items") or []:
        name = item.get("name") or "delivery item"
        if item.get("quantity") is not None:
            evidence.append({"field": "quantity", "item": name, "value": f"{item['quantity']} {item.get('unit') or ''}".strip(), "source": "delivery_challan", "quality": confidence_label(item.get("confidence"))})
        if item.get("condition"):
            evidence.append({"field": "condition", "item": name, "value": item["condition"], "source": "delivery_challan", "quality": confidence_label(item.get("confidence"))})
    return evidence


def voice_provenance(transcript: str, voice_amount_claim: dict | None = None) -> dict:
    val_str = transcript
    if voice_amount_claim and voice_amount_claim.get("value") is not None:
        prec = voice_amount_claim.get("precision", "exact")
        amt = voice_amount_claim["value"]
        orig = voice_amount_claim.get("original_text", "")
        prefix = "Approximately " if prec == "approximate" else ""
        orig_suffix = f' (phrase: "{orig}")' if orig else ""
        val_str = f'{transcript} [Voice Amount: {prefix}₹{amt:,.2f} INR{orig_suffix}]'
    return {"field": "foreman_report", "value": val_str, "source": "voice_note", "timestamp": "00:00 (full transcript)", "quality": "MEDIUM"}


def rule_based_question(conflicts: list[dict], missing: list[str], amount_recon: dict | None = None) -> str:
    fields = " ".join(clean_text(c.get("field")) for c in conflicts)
    if "quantity" in fields or "count" in fields:
        return "Physically count the delivered bags with the foreman and record the confirmed quantity."
    if any(word in fields for word in ("condition", "damage", "wet", "broken")):
        return "Inspect the reported damaged material and attach a site photograph before payment review."
    if "supplier" in fields:
        return "Verify the supplier name against the purchase order before payment review."

    # Handle Amount Reconciliation Ask Next wording specifically
    if amount_recon:
        status = amount_recon.get("status")
        if status == "MATCH_WITHIN_TOLERANCE":
            return "No additional verification required for the amount discrepancy; the approximate voice amount is within the configured tolerance."
        elif status == "CONFLICT":
            return "Confirm the exact bill amount with the foreman before final payment approval."
            
    if missing:
        non_critical = any(word in " ".join(clean_text(m) for m in missing) for word in ("supplier", "date", "unknowns", "header", "mode", "place"))
        if not non_critical:
            return "Request a clearer challan photo or a precise foreman confirmation for the missing evidence."
    return "Ask the site supervisor to review the source evidence before taking any payment action."


def is_material_conflict(c: dict) -> bool:
    why = str(c.get("why") or "").lower()
    field = str(c.get("field") or "").lower()
    if any(w in why or w in field for w in ("detail", "specification", "diameter", "breakdown", "sub-type", "formatting")):
        if not any(w in why for w in ("shortage", "different", "mismatch", "less", "more", "wrong", "damage", "wet", "broken")):
            return False
    return True


def safe_result(document: dict, transcript: str, model_result: dict) -> dict:
    """Apply non-negotiable application rules to model-proposed conflicts & Hindi number normalization."""
    # 1. Hindi/Hinglish Number Normalization
    voice_amount_claim = normalize_hindi_numbers(transcript)

    # 2. Evaluate Amount Alignment
    doc_amount = document.get("amount") or {}
    amount_recon = evaluate_amount_reconciliation(doc_amount, voice_amount_claim)

    raw_conflicts = [c for c in (model_result.get("conflicts") or []) if isinstance(c, dict)]

    # Process amount conflict based on amount_recon status
    conflicts: list[dict] = []
    for c in raw_conflicts:
        field_lower = str(c.get("field") or "").lower()
        if "amount" in field_lower:
            if amount_recon["status"] in ("MATCH", "MATCH_WITHIN_TOLERANCE"):
                continue  # Suppress pseudo amount conflict
            else:
                conflicts.append(c)
        elif is_material_conflict(c):
            conflicts.append(c)

    # If amount_recon is CONFLICT and no conflict was in model_result, add explicit conflict
    if amount_recon["status"] == "CONFLICT":
        has_amt_conflict = any("amount" in str(c.get("field") or "").lower() for c in conflicts)
        if not has_amt_conflict:
            conflicts.append({
                "field": "amount",
                "document_claim": f"₹{amount_recon['document_amount']} INR",
                "voice_claim": f"₹{amount_recon['voice_amount']} INR ({amount_recon['precision']})",
                "why": f"Voice amount differs from challan total by ₹{amount_recon['difference']} ({amount_recon['difference_percent']}%), exceeding configured {APPROX_AMOUNT_TOLERANCE_PERCENT}% tolerance."
            })

    # Filter missing information
    missing = list(model_result.get("missing_information") or [])
    for item in document.get("items") or []:
        if item.get("quantity") is None:
            missing.append(f"Readable quantity for {item.get('name') or 'delivery item'}")
        conf = item.get("confidence")
        conf_val = float(conf) if conf is not None else 0.95
        if conf_val < 0.70:
            missing.append(f"Clear reading of {item.get('name') or 'delivery item'}")
    missing.extend(document.get("unknowns") or [])
    missing = list(dict.fromkeys(str(x) for x in missing if str(x).strip()))

    # Filter critical missing
    critical_missing = []
    ignored_keywords = (
        "supplier", "vendor", "trader", "organization", "header",
        "date", "time", "amount", "currency", "price", "cost", "total",
        "transport", "vehicle", "place", "supply", "gst", "po",
        "challan number", "invoice number", "receipt number", "stamp", "signature",
        "mode", "location", "address", "terms", "payment", "breakdown", "specification", "diameter"
    )
    for m in missing:
        m_lower = m.lower()
        if "amount confirmation is missing" in m_lower:
            critical_missing.append(m)
        elif any(w in m_lower for w in ("damage", "wet", "broken", "torn", "defect", "leak", "spill", "shortage", "unreadable", "missing quantity", "quantity mismatch")):
            critical_missing.append(m)
        elif any(w in m_lower for w in ignored_keywords):
            continue
        elif any(p in m_lower for p in ("no missing", "no conflict", "none", "n/a", "no issues", "not stated")):
            continue
        elif "condition" in m_lower and not any(w in m_lower for w in ("damage", "wet", "broken", "torn", "defect", "leak", "spill", "shortage")):
            continue
        else:
            critical_missing.append(m)

    score = evidence_score(document, transcript, conflicts)

    # Check if amount is valid for proceed recommendation
    if amount_recon["status"] == "UNVERIFIED" and doc_amount and doc_amount.get("value") is not None:
        amount_is_valid = False
    else:
        amount_is_valid = amount_recon["status"] != "CONFLICT"

    can_proceed = not conflicts and not critical_missing and score["level"] == "HIGH" and amount_is_valid

    reasoning = (
        "Evidence is consistent and complete enough for a human to consider payment."
        if can_proceed else
        "Payment must remain on hold because evidence conflicts, is incomplete, or is not sufficiently readable."
    )

    return {
        "decision": "RECOMMEND_PROCEED" if can_proceed else "HOLD_FOR_REVIEW",
        "decision_basis": "deterministic_safety_policy",
        "evidence_quality": score,
        "conflicts": conflicts,
        "agreements": model_result.get("agreements") or [],
        "missing_information": missing,
        "amount_reconciliation": amount_recon,
        "voice_amount_claim": voice_amount_claim,
        "review_question": rule_based_question(conflicts, critical_missing, amount_recon),
        "reasoning_summary": reasoning,
        "provenance": document_provenance(document) + [voice_provenance(transcript, voice_amount_claim)],
    }


def pending_review(reason: str, document: dict | None = None, transcript: str = "") -> dict:
    """A safe, usable result for model or network failure."""
    return {
        "decision": "PENDING_REVIEW",
        "decision_basis": "safe_degradation",
        "evidence_quality": {"score": 0, "level": "LOW", "factors": [{"factor": reason, "impact": -100}]},
        "conflicts": [],
        "agreements": [],
        "missing_information": [reason],
        "review_question": "Keep payment on hold and retry analysis when the evidence service is available.",
        "reasoning_summary": "No payment recommendation was made because Sakshi could not safely complete the analysis.",
        "provenance": document_provenance(document or {}) + ([voice_provenance(transcript)] if transcript else []),
    }
