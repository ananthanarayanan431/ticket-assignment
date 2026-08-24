from .security import UNTRUSTED_CONTENT_NOTICE, wrap_untrusted

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


def build_classify_prompt(subject: str, body: str) -> tuple[str, str]:
    categories = ", ".join(CATEGORIES)
    system_prompt = (
        f"Classify this support ticket into exactly one of these categories: {categories}.\n\n"
        "Category definitions:\n"
        "- billing: anything involving money — invoices, charges, refunds, cancellations, pricing.\n"
        "- account_deletion: the customer wants their account or personal data deleted.\n"
        "- legal: legal threats, formal compliance requests (e.g. GDPR/CCPA citations), subpoenas.\n"
        "- security: a reported vulnerability or security incident, not a routine login problem.\n"
        "- bug: something in the product is broken or not working as expected.\n"
        "- feature_request: a request for new or changed functionality.\n"
        "- account_access: login, password reset, or account-lockout issues with no security "
        "vulnerability implicated.\n"
        "- spam: unsolicited/promotional content unrelated to support.\n"
        "- other: anything that doesn't fit the above (e.g. general feedback, thanks).\n\n"
        "If the ticket raises multiple issues, choose the category of the most sensitive issue "
        "present (e.g. a bug report that also mentions being double-charged is billing, not bug).\n\n"
        "confidence must reflect only how certain you are of the category — "
        "never lower it because the customer sounds upset, frustrated, or angry. "
        "An angry customer with a simple request (e.g. an address change) is still "
        "a simple, high-confidence request; tone is not evidence of complexity. "
        "Return JSON with keys: category, confidence (0-1).\n\n"
        f"{UNTRUSTED_CONTENT_NOTICE}"
    )
    user_content = wrap_untrusted("ticket", f"Subject: {subject}\nBody: {body}")
    return system_prompt, user_content
