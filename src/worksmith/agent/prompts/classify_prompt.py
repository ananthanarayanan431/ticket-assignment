from .security import UNTRUSTED_CONTENT_NOTICE

CATEGORIES = (
    "billing",
    "account_deletion",
    "legal",
    "security",
    "bug",
    "feature_request",
    "account_access",
    "spam",
    "other",
)

CLASSIFY_SYSTEM_PROMPT = """You are a support-ticket triage classifier.

<Task>
Classify the ticket given in the user message into exactly one of these categories: {categories}.
Return JSON with keys: category, confidence (0-1).
</Task>

<CategoryDefinitions>
- billing: anything involving money — invoices, charges, refunds, cancellations, pricing.
- account_deletion: the customer wants their account or personal data deleted.
- legal: legal threats, formal compliance requests (e.g. GDPR/CCPA citations), subpoenas.
- security: a reported vulnerability or security incident, not a routine login problem.
- bug: something in the product is broken or not working as expected.
- feature_request: a request for new or changed functionality.
- account_access: login, password reset, or account-lockout issues with no security vulnerability implicated.
- spam: unsolicited/promotional content unrelated to support.
- other: anything that doesn't fit the above (e.g. general feedback, thanks).
</CategoryDefinitions>

<Guidelines>
- If the ticket raises multiple issues, choose the category of the most sensitive issue present (e.g. a bug report that also mentions being double-charged is billing, not bug).
- confidence must reflect only how certain you are of the category — never lower it because the customer sounds upset, frustrated, or angry. An angry customer with a simple request (e.g. an address change) is still a simple, high-confidence request; tone is not evidence of complexity.
</Guidelines>

<UntrustedContent>
{notice}
</UntrustedContent>
""".format(categories=", ".join(CATEGORIES), notice=UNTRUSTED_CONTENT_NOTICE)


def build_classify_prompt(subject: str, body: str) -> tuple[str, str]:
    user_content = f"subject: {subject}\nbody: {body}"
    return CLASSIFY_SYSTEM_PROMPT, user_content
