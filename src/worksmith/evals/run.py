"""
Small eval harness: runs the real graph (same code path as production) over
a hand-labeled subset of the sample tickets and grades the output with an
LLM judge, so regressions in prompts/routing logic are visible before they
ship.

    uv run python -m worksmith.evals.run
"""

import asyncio
import json
from importlib import resources
from pathlib import Path

from ..agent.graph import build_graph
from ..db.checkpointer import get_checkpointer
from ..db.postgres import dispose_engine
from ..agent.review import load_tickets
from .grade import grade_ticket
from .schema import GoldLabel

GOLDEN_FILE = resources.files("worksmith.evals").joinpath("golden_tickets.json")
RESULTS_DIR = Path(__file__).parent / "results"

# Eval runs use their own ticket/thread-id namespace so they never collide
# with real tickets sitting in the production `tickets` table or checkpointer.
EVAL_ID_PREFIX = "EVAL-"


def load_golden_dataset() -> list[dict]:
    return json.loads(GOLDEN_FILE.read_text())


async def run_eval() -> list[dict]:
    tickets_by_id = {t["id"]: t for t in load_tickets()}
    golden = load_golden_dataset()

    results = []
    async with get_checkpointer() as checkpointer:
        graph = build_graph(checkpointer)
        for entry in golden:
            ticket = tickets_by_id[entry["ticket_id"]]
            gold = GoldLabel.model_validate(entry["gold"])

            config = {"configurable": {"thread_id": f"{EVAL_ID_PREFIX}{ticket['id']}"}}
            initial_state = {
                "ticket_id": f"{EVAL_ID_PREFIX}{ticket['id']}",
                "from_name": ticket["from_name"],
                "from_email": ticket["from_email"],
                "subject": ticket["subject"],
                "body": ticket["body"],
            }
            actual = await graph.ainvoke(initial_state, config=config)
            verdict = await grade_ticket(gold, actual)

            results.append({"ticket_id": ticket["id"], "gold": gold, "actual": actual, "verdict": verdict})
    return results


def summarize(results: list[dict]) -> dict:
    n = len(results)
    category_correct = sum(1 for r in results if r["verdict"].category_correct)
    decision_correct = sum(1 for r in results if r["verdict"].decision_correct)
    mean_extraction_score = sum(r["verdict"].extraction_score for r in results) / n if n else 0.0
    violations = [
        r["ticket_id"]
        for r in results
        if not r["verdict"].decision_correct and "HARD CONSTRAINT VIOLATION" in r["verdict"].decision_feedback
    ]
    return {
        "n": n,
        "category_accuracy": category_correct / n if n else 0.0,
        "decision_accuracy": decision_correct / n if n else 0.0,
        "mean_extraction_score": mean_extraction_score,
        "hard_constraint_violations": violations,
    }


def _result_to_json(r: dict) -> dict:
    return {
        "ticket_id": r["ticket_id"],
        "gold": r["gold"].model_dump(),
        "actual": {
            "category": r["actual"].get("category"),
            "decision": r["actual"].get("decision"),
            "confidence": r["actual"].get("confidence"),
            "extracted_fields": r["actual"].get("extracted_fields"),
            "interrupted": "__interrupt__" in r["actual"],
        },
        "verdict": r["verdict"].model_dump(),
    }


def write_report(results: list[dict], summary: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "latest.json"
    payload = {"summary": summary, "results": [_result_to_json(r) for r in results]}
    path.write_text(json.dumps(payload, indent=2))
    return path


def print_report(results: list[dict], summary: dict, path: Path) -> None:
    print(f"{'ticket_id':<10} {'category ok':<12} {'decision ok':<12} {'extraction':<10} notes")
    for r in results:
        v = r["verdict"]
        flag = " ⚠ HARD CONSTRAINT VIOLATION" if "HARD CONSTRAINT VIOLATION" in v.decision_feedback else ""
        print(
            f"{r['ticket_id']:<10} {str(v.category_correct):<12} {str(v.decision_correct):<12} "
            f"{v.extraction_score:<10.2f}{flag}"
        )

    print()
    print(f"n={summary['n']}  category_accuracy={summary['category_accuracy']:.0%}  "
          f"decision_accuracy={summary['decision_accuracy']:.0%}  "
          f"mean_extraction_score={summary['mean_extraction_score']:.2f}")
    if summary["hard_constraint_violations"]:
        print(f"HARD CONSTRAINT VIOLATIONS: {summary['hard_constraint_violations']}")
    else:
        print("No hard-constraint violations.")
    print(f"\nFull report written to {path}")


async def main() -> None:
    results = await run_eval()
    summary = summarize(results)
    path = write_report(results, summary)
    print_report(results, summary, path)
    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
