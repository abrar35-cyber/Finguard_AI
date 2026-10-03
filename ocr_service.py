import re

import pytesseract
from PIL import Image

KNOWN_PROVIDERS = {
    "K-Electric": ["k-electric", "k electric", "kelectric"],
    "LESCO": ["lesco", "lahore electric"],
    "IESCO": ["iesco", "islamabad electric"],
    "FESCO": ["fesco"],
    "MEPCO": ["mepco"],
    "HESCO": ["hesco"],
    "SSGC": ["ssgc", "sui southern"],
    "SNGPL": ["sngpl", "sui northern"],
    "PTCL": ["ptcl"],
    "StormFiber": ["stormfiber", "storm fiber"],
    "Nayatel": ["nayatel"],
    "KWSB": ["kwsb", "karachi water"],
}


def extract_text_from_image(uploaded_file):
    try:
        uploaded_file.seek(0)  # st.image() may have moved the pointer
    except Exception:
        pass

    image = Image.open(uploaded_file).convert("RGB")
    text = pytesseract.image_to_string(image)
    return text.strip()


def detect_provider(text):
    """Return a known provider name found in the text, or empty string."""
    lowered = (text or "").lower()
    for name, keywords in KNOWN_PROVIDERS.items():
        if any(k in lowered for k in keywords):
            return name
    return ""


def extract_amount(text):
    """Pick the payable amount. Prefers numbers near 'payable', 'total' or 'amount due'."""
    if not text:
        return 0.0

    number = r"(?:Rs\.?|PKR)?\s*([0-9]{1,3}(?:,[0-9]{3})+(?:\.\d{1,2})?|[0-9]+(?:\.\d{1,2})?)"
    keywords = r"(?:payable|total|amount\s*due|net\s*amount|bill\s*amount)[^0-9\n]{0,25}"

    for match in re.finditer(keywords + number, text, flags=re.IGNORECASE):
        try:
            value = float(match.group(1).replace(",", ""))
            if value > 0:
                return value
        except ValueError:
            continue

    # Fallback: largest number that looks like money
    candidates = []
    for m in re.finditer(number, text):
        try:
            candidates.append(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    candidates = [c for c in candidates if 10 <= c <= 10_000_000]
    return max(candidates) if candidates else 0.0


def extract_consumer_number(text):
    """Find a consumer / account / reference number."""
    if not text:
        return ""

    labelled = re.search(
        r"(?:consumer|account|reference|ref|customer)\s*(?:no|number|#|id)?\.?\s*[:\-]?\s*([0-9][0-9\- ]{6,20}[0-9])",
        text,
        flags=re.IGNORECASE,
    )
    if labelled:
        return labelled.group(1).strip()

    long_number = re.search(r"\b\d{10,14}\b", text)
    return long_number.group(0) if long_number else ""
