from groq_service import extract_bill_with_groq


def analyze_bill(raw_bill):

    """
    Analyze a raw bill using Groq and return
    structured bill information.
    """

    if not raw_bill:
        return None

    text = raw_bill.get("content", "")

    if not text:
        text = raw_bill.get("text", "")

    if not text:
        text = str(raw_bill)

    result = extract_bill_with_groq(text)

    if not result:
        return None

    result["source"] = raw_bill.get(
        "source",
        "demo"
    )

    return result
