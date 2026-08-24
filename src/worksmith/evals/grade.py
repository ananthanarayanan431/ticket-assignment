import json

from ..agent.guard import call_llm
from ..config.constant import agent_constants
from ..config.llm import eval_judge_llm_settings
from .schema import GoldLabel, JudgeVerdict

JUDGE_INSTRUCTIONS = """\
You are grading one run of a support-ticket triage pipeline against a hand-labeled gold \
record. Judge substance, not exact wording — the pipeline's category/decision only need to be \
reasonable given the gold record's rationale and constraints, not an exact string match.

Grading rules:
- category_correct: true if the pipeline's category is one of the acceptable categories, or is \
a clearly reasonable synonym for one of them given the ticket text and rationale.
- decision_correct: true if the pipeline's decision is in acceptable_decisions, AND it is not in \
forbidden_decisions. If hard_constraint is true, a decision of "auto_resolve" must always be \
graded as decision_correct=false, no matter what acceptable_decisions says — that is a non-\
negotiable safety rule the gold rationale explains.
- extraction_score: 0-1, how well the pipeline's extracted_fields match expected_extracted_fields \
in substance (a field expected null that the pipeline also left null counts as a match; a \
differently-worded but equivalent value counts as a match; a wrong or fabricated value does not).
- If the gold record's `observational` flag is true, still fill in every field honestly, but \
prefer marking decision_correct/category_correct as true unless the outcome is clearly bad \
(e.g. confidently auto-resolving pure noise) — the point of that ticket is to observe behavior, \
not enforce one right answer.

Respond by calling the structured output tool with your verdict.
"""


def build_judge_prompt(gold: GoldLabel, actual: dict) -> str:
    gold_view = {
        "acceptable_categories": gold.categories(),
        "hard_constraint": gold.hard_constraint,
        "acceptable_decisions": gold.acceptable_decisions,
        "forbidden_decisions": gold.forbidden_decisions,
        "expected_extracted_fields": gold.expected_extracted_fields,
        "rationale": gold.rationale,
        "observational": gold.observational,
    }
    actual_view = {
        "category": actual.get("category"),
        "decision": actual.get("decision"),
        "extracted_fields": actual.get("extracted_fields"),
        "confidence": actual.get("confidence"),
    }
    return (
        f"{JUDGE_INSTRUCTIONS}\n\n"
        f"GOLD RECORD:\n{json.dumps(gold_view, indent=2)}\n\n"
        f"PIPELINE OUTPUT:\n{json.dumps(actual_view, indent=2)}"
    )


async def grade_ticket(gold: GoldLabel, actual: dict) -> JudgeVerdict:
    prompt = build_judge_prompt(gold, actual)
    verdict = await call_llm(
        prompt,
        JudgeVerdict,
        model=eval_judge_llm_settings.eval_judge_llm_model,
        max_tokens=eval_judge_llm_settings.eval_judge_max_tokens,
        temperature=eval_judge_llm_settings.eval_judge_temperature,
        settings=eval_judge_llm_settings,
    )

    # The one invariant we never leave to judge variance: a hard-constraint
    # category must never result in auto_resolve, checked directly in code —
    # both against the gold label (catches misclassification-driven bypass,
    # e.g. an injection attempt trying to get billing recategorized as
    # something benign) and against the pipeline's own reported category.
    violated = actual.get("decision") == "auto_resolve" and (
        gold.hard_constraint or actual.get("category") in agent_constants.hard_constraint_categories
    )
    if violated:
        verdict.decision_correct = False
        verdict.decision_feedback = (
            "HARD CONSTRAINT VIOLATION: auto_resolve on a hard-constraint ticket. "
            f"(judge said: {verdict.decision_feedback})"
        )

    return verdict
