def build_draft_for_review_prompt(category: str, extracted_fields: dict, body: str) -> str:
    return (
        f"Draft a personalized reply for this {category} ticket. "
        f"Fields: {extracted_fields}\nBody: {body}"
    )
