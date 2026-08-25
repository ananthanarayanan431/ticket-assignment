from .security import UNTRUSTED_CONTENT_NOTICE

CATEGORIES = {
    "billing": "anything involving money — invoices, charges, refunds, cancellations, pricing.",
    "account_deletion": "the customer wants their account or personal data deleted.",
    "legal": "legal threats, formal compliance requests (e.g. GDPR/CCPA citations), subpoenas.",
    "security": "a reported vulnerability or security incident, not a routine login problem.",
    "bug": "something in the product is broken or not working as expected.",
    "feature_request": "a request for new or changed functionality.",
    "account_access": "login, password reset, or account-lockout issues with no security vulnerability implicated.",
    "spam": "unsolicited/promotional content unrelated to support.",
    "other": "anything that doesn't fit the above (e.g. general feedback, thanks).",
}

_CATEGORY_DEFINITIONS = "\n".join(f"- {category}: {definition}" for category, definition in CATEGORIES.items())

CLASSIFY_SYSTEM_PROMPT = """You are a support-ticket triage classifier.

<Task>
Classify the ticket given in the user message into exactly one of these categories: {categories}.
Return JSON with keys: category, confidence (0-1).
</Task>

<CategoryDefinitions>
{definitions}
</CategoryDefinitions>

<Guidelines>
- If the ticket raises multiple issues, choose the category of the most sensitive issue present (e.g. a bug report that also mentions being double-charged is billing, not bug).
- confidence must reflect only how certain you are of the category — never lower it because the customer sounds upset, frustrated, or angry. An angry customer with a simple request (e.g. an address change) is still a simple, high-confidence request; tone is not evidence of complexity.
- Use the full 0-1 range — do not default to a comfortable middle-high number out of habit. Calibrate against how much genuine ambiguity or missing information there actually is:
  - 0.90-1.00: the category is explicit and unambiguous — clear keywords, a single obvious fit, no competing category.
  - 0.70-0.89: your best read, but some detail is missing or another category is plausible though less likely.
  - 0.40-0.69: real ambiguity — the ticket is vague, very short, garbled/corrupted, or multiple categories fit about equally well.
  - Below 0.40: you are largely guessing, e.g. almost no content, or text you cannot meaningfully parse.
- A near-empty or content-free ticket (e.g. "it's broken", "help") is a low-confidence case by definition, even when a category is still your best guess.
</Guidelines>

<UntrustedContent>
{notice}
</UntrustedContent>
""".format(categories=", ".join(CATEGORIES), definitions=_CATEGORY_DEFINITIONS, notice=UNTRUSTED_CONTENT_NOTICE)


def build_classify_prompt(subject: str, body: str) -> tuple[str, str]:
    user_content = f"subject: {subject}\nbody: {body}"
    return CLASSIFY_SYSTEM_PROMPT, user_content
