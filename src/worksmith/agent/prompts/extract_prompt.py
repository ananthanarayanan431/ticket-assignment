def build_extract_prompt(category: str, subject: str, body: str) -> str:
    return (
        f"Extract structured fields for this {category} ticket. "
        "Return JSON with keys: extracted_fields (object with account_identifier, "
        "product_area, urgency, sentiment — null for any not mentioned), confidence (0-1).\n\n"
        "sentiment and urgency are independent: sentiment is the customer's tone "
        "(angry, neutral, happy, ...); urgency is how time-sensitive or high-impact "
        "the underlying request actually is. A furious customer asking for a simple "
        "address change is negative sentiment but low urgency — do not inflate urgency "
        "just because the tone is negative.\n\n"
        f"Subject: {subject}\nBody: {body}"
    )
