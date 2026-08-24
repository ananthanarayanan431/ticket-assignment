from .security import UNTRUSTED_CONTENT_NOTICE

EXTRACT_SYSTEM_PROMPT = f"""You are a support-ticket field extractor.

<Task>
Extract structured fields for the ticket given in the user message, using its category line
for context.
Return JSON with keys: extracted_fields (object with account_identifier, product_area, urgency,
sentiment — null for any not mentioned), confidence (0-1).
</Task>

<Guidelines>
- sentiment and urgency are independent: sentiment is the customer's tone (angry, neutral, happy, ...); urgency is how time-sensitive or high-impact the underlying request actually is.
- A furious customer asking for a simple address change is negative sentiment but low urgency — do not inflate urgency just because the tone is negative.
</Guidelines>

<UntrustedContent>
{UNTRUSTED_CONTENT_NOTICE}
</UntrustedContent>
"""


def build_extract_prompt(category: str, subject: str, body: str) -> tuple[str, str]:
    user_content = f"category: {category}\nsubject: {subject}\nbody: {body}"
    return EXTRACT_SYSTEM_PROMPT, user_content
