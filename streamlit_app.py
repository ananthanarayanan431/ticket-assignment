"""
Human-in-the-loop review UI.

    uv run streamlit run streamlit_app.py
"""

import asyncio

import streamlit as st

from worksmith import review
from worksmith.agent.graph import build_graph
from worksmith.db.checkpointer import get_checkpointer
from worksmith.db.postgres import dispose_engine

st.set_page_config(page_title="Ticket Triage — Human Review", layout="wide")


def call(fn):
    """
    Run `fn(graph)` in a fresh event loop with a fresh checkpointer/engine.
    Streamlit reruns this whole script on every interaction, possibly from a
    different thread each time, and asyncpg/SQLAlchemy connections are bound
    to the loop that created them — so nothing async can be cached across
    reruns; everything is opened and disposed per call.
    """

    async def _run():
        async with get_checkpointer() as checkpointer:
            graph = build_graph(checkpointer)
            result = await fn(graph)
        await dispose_engine()
        return result

    return asyncio.run(_run())


def call_db(fn):
    """Same as `call`, but for operations that only touch Postgres, not the graph."""

    async def _run():
        result = await fn()
        await dispose_engine()
        return result

    return asyncio.run(_run())


async def _run_many(graph, tickets: list[dict]) -> dict[str, dict]:
    return {ticket["id"]: await review.run_ticket(graph, ticket) for ticket in tickets}


def _report_run_results(results: dict[str, dict]) -> None:
    for ticket_id, result in results.items():
        if "__interrupt__" in result:
            st.info(f"{ticket_id}: paused for human review")
        else:
            st.success(f"{ticket_id}: {result.get('decision')} — {result.get('response_text')!r}")


st.title("Support Ticket Triage")

with st.expander("Run tickets through the pipeline"):
    tickets = review.load_tickets()
    options = {t["id"]: t for t in tickets}
    selected = st.multiselect("Tickets", options=list(options.keys()))

    col1, col2 = st.columns(2)
    if col1.button("Run selected", disabled=not selected):
        _report_run_results(call(lambda graph: _run_many(graph, [options[i] for i in selected])))
    if col2.button("Run all"):
        _report_run_results(call(lambda graph: _run_many(graph, tickets)))

st.divider()

tab_escalations, tab_drafts = st.tabs(["🚨 Escalations", "📝 Drafts for review"])

with tab_escalations:
    escalations = call(review.list_escalations)
    if not escalations:
        st.write("Nothing pending.")
    for esc in escalations:
        with st.container(border=True):
            st.subheader(esc["ticket_id"])
            st.caption(f"Category: {esc.get('category')} · Reason: {esc.get('reason')}")
            st.write(f"**From:** {esc.get('from_name')} <{esc.get('from_email')}>")
            st.write(f"**Subject:** {esc.get('subject')}")
            st.write(esc.get("body"))

            response = st.text_area("Response to send", key=f"resp_{esc['ticket_id']}")
            resolved_by = st.text_input("Your name/email", key=f"by_{esc['ticket_id']}")

            c1, c2 = st.columns(2)
            if c1.button("Send response", key=f"send_{esc['ticket_id']}", disabled=not response):
                call(lambda graph, tid=esc["ticket_id"]: review.resolve_escalation(graph, tid, response, resolved_by))
                st.rerun()
            if c2.button("Reject / close", key=f"reject_{esc['ticket_id']}"):
                call(lambda graph, tid=esc["ticket_id"]: review.resolve_escalation(graph, tid, None, resolved_by))
                st.rerun()

with tab_drafts:
    drafts = call_db(review.list_drafts)
    if not drafts:
        st.write("Nothing pending.")
    for row in drafts:
        with st.container(border=True):
            st.subheader(row.ticket_id)
            edited = st.text_area("Draft response", value=row.response_text or "", key=f"draft_{row.ticket_id}")

            c1, c2 = st.columns(2)
            if c1.button("Approve / save", key=f"approve_{row.ticket_id}"):
                call_db(lambda tid=row.ticket_id, text=edited: review.resolve_draft(tid, text, reject=False))
                st.rerun()
            if c2.button("Reject", key=f"draft_reject_{row.ticket_id}"):
                call_db(lambda tid=row.ticket_id: review.resolve_draft(tid, None, reject=True))
                st.rerun()
