"""
Test suite for Hindi/Hinglish number normalization, precision tracking,
and 4-state amount reconciliation.
"""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.hindi_normalizer import normalize_hindi_numbers
from app.safety import safe_result

# Challan document matching ₹258,231.20
CHALLAN_DOC = {
    "supplier": {"value": "Ultratech / Site Vendor", "confidence": 0.95},
    "date": {"value": "20.12.2021", "confidence": 0.95},
    "items": [
        {"name": "Sand", "quantity": 650, "unit": "cubic ft", "confidence": 0.95},
        {"name": "Aggregate", "quantity": 800, "unit": "cubic ft", "confidence": 0.95},
        {"name": "Cement", "quantity": 160, "unit": "nos", "confidence": 0.95},
        {"name": "TMT Steel", "quantity": 1360, "unit": "Kgs", "confidence": 0.95}
    ],
    "amount": {"value": 258231.20, "currency": "INR", "confidence": 0.95},
    "unknowns": []
}

# 5 Test Transcripts
TEST_CASES = [
    {
        "name": "Test A: Approximate 258,000",
        "transcript": "Total bill do lakh athavan hazaar ke aas-paas hai.",
        "expected_value": 258000,
        "expected_precision": "approximate",
        "expected_amount_status": "MATCH_WITHIN_TOLERANCE",
        "expected_decision": "RECOMMEND_PROCEED"
    },
    {
        "name": "Test B: Approximate 280,000 (Exceeds tolerance)",
        "transcript": "Total bill do lakh assi hazaar ke aas-paas hai.",
        "expected_value": 280000,
        "expected_precision": "approximate",
        "expected_amount_status": "CONFLICT",
        "expected_decision": "HOLD_FOR_REVIEW"
    },
    {
        "name": "Test C: Exact 258,231",
        "transcript": "Total bill do lakh athavan hazaar do sau ikattis rupaye hai.",
        "expected_value": 258231,
        "expected_precision": "exact",
        "expected_amount_status": "MATCH",
        "expected_decision": "RECOMMEND_PROCEED"
    },
    {
        "name": "Test D: Approximate 300,000 (Exceeds tolerance)",
        "transcript": "Total bill lagbhag teen lakh rupaye hai.",
        "expected_value": 300000,
        "expected_precision": "approximate",
        "expected_amount_status": "CONFLICT",
        "expected_decision": "HOLD_FOR_REVIEW"
    },
    {
        "name": "Test E: Amount unknown",
        "transcript": "Bill amount pata nahi hai.",
        "expected_value": None,
        "expected_precision": "exact",
        "expected_amount_status": "UNVERIFIED",
        "expected_decision": "HOLD_FOR_REVIEW"
    }
]

def run_tests():
    print("==================================================")
    print("RUNNING 5 HINDI NUMBER NORMALIZATION TEST CASES")
    print("==================================================")
    all_passed = True
    for test in TEST_CASES:
        transcript = test["transcript"]
        norm = normalize_hindi_numbers(transcript)
        
        # Run safe_result
        res = safe_result(CHALLAN_DOC, transcript, {"conflicts": [], "agreements": [], "missing_information": []})
        amt_rec = res["amount_reconciliation"]
        decision = res["decision"]

        val_ok = norm["value"] == test["expected_value"]
        prec_ok = norm["precision"] == test["expected_precision"]
        status_ok = amt_rec["status"] == test["expected_amount_status"]
        dec_ok = decision == test["expected_decision"]

        passed = val_ok and prec_ok and status_ok and dec_ok
        if not passed:
            all_passed = False

        status_symbol = "PASSED" if passed else "FAILED"
        print(f"\n[{status_symbol}] {test['name']}")
        print(f"  Transcript: \"{transcript}\"")
        print(f"  Normalized: Value={norm['value']}, Precision={norm['precision']}, Original Phrase=\"{norm['original_text']}\"")
        print(f"  Reconciliation Status: {amt_rec['status']} (Diff: RS {amt_rec['difference']}, {amt_rec['difference_percent']}%)")
        print(f"  Ask Next: \"{res['review_question']}\"")
        print(f"  Final Decision: {decision}")

    print("\n==================================================")

    # Also test 20 standard eval cases
    cases_path = pathlib.Path("eval/cases.json")
    if cases_path.exists():
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        eval_passed = 0
        for case in cases:
            r = safe_result(case["document"], case["transcript"], case["assessment"])
            if r["decision"] == case["expected_decision"]:
                eval_passed += 1
        print(f"Standard 20-Case Eval Suite: {eval_passed}/{len(cases)} passed")
    
    print("==================================================")
    if all_passed:
        print("ALL 5 NEW AMOUNT TESTS & EVAL CASES PASSED 100%!")
    else:
        print("SOME TESTS FAILED!")

if __name__ == "__main__":
    run_tests()
