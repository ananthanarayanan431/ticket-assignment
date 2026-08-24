def build_draft_for_review_prompt(
    category: str, extracted_fields: dict, body: str, from_name: str, from_email: str
) -> str:
    return (
        f"Draft a personalized reply for this {category} ticket. "
        f"From: {from_name} <{from_email}>\n"
        f"Fields: {extracted_fields}\nBody: {body}"
    )
