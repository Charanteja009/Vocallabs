"""Hindi and Hinglish Number Normalizer for Sakshi Audio & Text Claims."""
import re
from typing import Any, Dict, Optional

NUMBER_MAP: Dict[str, int] = {
    'shunya': 0, 'zero': 0, '0': 0,
    'ek': 1, 'one': 1, '1': 1,
    'do': 2, 'two': 2, '2': 2,
    'teen': 3, 'three': 3, '3': 3,
    'char': 4, 'chaar': 4, 'four': 4, '4': 4,
    'paanch': 5, 'panch': 5, 'five': 5, '5': 5,
    'chhe': 6, 'chha': 6, 'six': 6, '6': 6,
    'saat': 7, 'seven': 7, '7': 7,
    'aath': 8, 'eight': 8, '8': 8,
    'nau': 9, 'nine': 9, '9': 9,
    'das': 10, 'ten': 10, '10': 10,
    'gyarah': 11, 'baarah': 12, 'terah': 13, 'chaudah': 14,
    'pandrah': 15, 'soolah': 16, 'solah': 16, 'satrah': 17, 'athtarah': 18, 'unnees': 19, 'bees': 20,
    'tees': 30, 'ikattis': 31, 'ikatis': 31, 'chaalis': 40, 'chalis': 40,
    'pachaas': 50, 'pachas': 50,
    'ikyaavan': 51, 'baavan': 52, 'tirpan': 53, 'chauvan': 54, 'pachpan': 55, 'chappan': 56, 'satavan': 57,
    'athavan': 58, 'athhavan': 58, 'atavan': 58, 'athwan': 58, '58': 58,
    'unsath': 59, 'saath': 60, 'sath': 60, 'sattar': 70,
    'ikyaasi': 81, 'byaasi': 82, 'tirasi': 83, 'chaurasi': 84, 'pachasi': 85, 'chhaasi': 86, 'sattaasi': 87, 'athtasi': 88, 'nawaasi': 89,
    'assi': 80, 'asi': 80, 'nabbe': 90
}

APPROX_WORDS = [
    'lagbhag', 'aas-paas', 'aas paas', 'around', 'approximately', 'approx',
    'kareeb', 'karib', 'लगभग', 'करीब', 'near', 'estimated'
]

UNKNOWN_WORDS = [
    'pata nahi', 'pata nahi hai', 'don\'t know', 'unknown', 'not mentioned',
    'no bill', 'not sure', 'pata nai', 'maloom nahi'
]

def word_to_num(val: Any) -> int:
    if val is None:
        return 0
    s = str(val).strip().lower()
    if s.isdigit():
        return int(s)
    return NUMBER_MAP.get(s, 0)

def normalize_hindi_numbers(transcript: str) -> Dict[str, Any]:
    """
    Normalizes spoken Hindi/Hinglish numeric claims in site reports into structured amount data.
    
    Returns dict:
    {
        "field": "amount",
        "value": int | float | None,
        "currency": "INR",
        "precision": "exact" | "approximate",
        "original_text": str
    }
    """
    if not transcript:
        return {
            "field": "amount",
            "value": None,
            "currency": "INR",
            "precision": "exact",
            "original_text": ""
        }

    text = transcript.strip()
    text_lower = text.lower()

    # 1. Unknown / Unstated check
    if any(p in text_lower for p in UNKNOWN_WORDS):
        return {
            "field": "amount",
            "value": None,
            "currency": "INR",
            "precision": "exact",
            "original_text": text
        }

    # 2. Approximation keyword check
    is_approx = any(w in text_lower for w in APPROX_WORDS)
    precision = "approximate" if is_approx else "exact"

    # 3. Pattern matching for Lakh + Hazaar + Sau + Tens (e.g. 'do lakh athavan hazaar do sau ikattis')
    pattern_lakh = r'(\d+|ek|do|teen|char|chaar|paanch|panch|chhe|saat|aath|nau|das)\s*lakh(?:s|ac|acs)?(?:\s*(\d+|athavan|athhavan|atavan|pachaas|pachas|saath|sath|sattar|assi|asi|nabbe|chaalis|chalis|tees|bees|das|gyarah|baarah|terah|chaudah|pandrah|soolah|solah|satrah|athtarah|unnees|\d+)\s*hazaar|hazar|thousand)?(?:\s*(\d+|ek|do|teen|char|chaar|paanch|panch)\s*sau|hundred)?(?:\s*(ikattis|ikatis|\d+))?'
    match_lakh = re.search(pattern_lakh, text_lower)
    if match_lakh:
        lakh_val = word_to_num(match_lakh.group(1)) * 100000
        hazar_val = word_to_num(match_lakh.group(2)) * 1000 if match_lakh.group(2) else 0
        sau_val = word_to_num(match_lakh.group(3)) * 100 if match_lakh.group(3) else 0
        tens_val = word_to_num(match_lakh.group(4)) if match_lakh.group(4) else 0

        total_val = lakh_val + hazar_val + sau_val + tens_val
        phrase = match_lakh.group(0).strip()
        return {
            "field": "amount",
            "value": total_val,
            "currency": "INR",
            "precision": precision,
            "original_text": phrase
        }

    # 4. Pattern matching for Hazaar only (e.g., 'pachaas hazaar')
    pattern_hazar = r'(\d+|athavan|athhavan|atavan|pachaas|pachas|saath|sath|sattar|assi|asi|nabbe|chaalis|chalis|tees|bees|das)\s*hazaar|hazar|thousand'
    match_hazar = re.search(pattern_hazar, text_lower)
    if match_hazar:
        h_val = word_to_num(match_hazar.group(1)) * 1000
        phrase = match_hazar.group(0).strip()
        return {
            "field": "amount",
            "value": h_val,
            "currency": "INR",
            "precision": precision,
            "original_text": phrase
        }

    # 5. Direct numerical digits pattern (e.g. ₹2,58,231.20 or 258000)
    num_match = re.search(r'₹?\s*([\d,]+(?:\.\d+)?)', text)
    if num_match:
        val_str = num_match.group(1).replace(',', '')
        try:
            val = float(val_str)
            return {
                "field": "amount",
                "value": int(val) if val.is_integer() else val,
                "currency": "INR",
                "precision": precision,
                "original_text": num_match.group(0).strip()
            }
        except ValueError:
            pass

    return {
        "field": "amount",
        "value": None,
        "currency": "INR",
        "precision": precision,
        "original_text": text
    }
