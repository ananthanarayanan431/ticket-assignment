"""
Human-in-the-loop review UI.

    uv run streamlit run streamlit_app.py
"""

import asyncio

import streamlit as st

from worksmith.agent import review
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


def _invalidate_queues():
    """Drop cached Escalations/Drafts/Sent so the next visit to those pages re-fetches."""
    st.session_state.pop("escalations", None)
    st.session_state.pop("drafts", None)
    st.session_state.pop("auto_resolved", None)


async def _run_many(graph, tickets: list[dict]) -> dict[str, dict]:
    return {ticket["id"]: await review.run_ticket(graph, ticket) for ticket in tickets}


def _render_run_result(ticket_id: str, result: dict) -> None:
    with st.container(border=True):
        st.markdown(f"#### {ticket_id}")

        interrupts = result.get("__interrupt__")
        if interrupts:
            payload = interrupts[0].value if isinstance(interrupts[0].value, dict) else {}
            reason = payload.get("reason")
            st.warning("🚨 Escalated for human review" + (f" — {reason}" if reason else ""))
            return

        decision = result.get("decision")
        category = result.get("category")
        confidence = result.get("confidence")

        status = {
            "auto_resolve": ("✅", "Auto-resolved — sent"),
            "draft_for_review": ("📝", "Drafted — pending review"),
            "escalate": ("🚨", "Escalated"),
        }.get(decision, ("❔", decision or "unknown"))
        st.markdown(f"{status[0]} **{status[1]}**")

        c1, c2 = st.columns(2)
        c1.metric("Category", category or "—")
        c2.metric("Confidence", f"{confidence:.0%}" if confidence is not None else "—")

        if result.get("response_text"):
            st.caption("Response")
            st.text(result["response_text"])


st.sidebar.title("Ticket Triage")
page = st.sidebar.radio(
    "Navigate",
    ["Run sample tickets", "Test a ticket manually", "Escalations", "Drafts for review", "Auto-resolved"],
    label_visibility="collapsed",
)

if page == "Run sample tickets":
    st.title("Run sample tickets")
    tickets = review.load_tickets()
    options = {t["id"]: t for t in tickets}
    selected = st.multiselect("Tickets", options=list(options.keys()))

    for tid in selected:
        t = options[tid]
        with st.expander(f"{tid} — {t['subject']}"):
            st.markdown(f"**From:** {t['from_name']} <{t['from_email']}>")
            st.markdown(t["body"])

    col1, col2 = st.columns(2)
    run_selected = col1.button("Run selected", disabled=not selected)
    run_all = col2.button("Run all")

    if run_selected or run_all:
        batch = [options[i] for i in selected] if run_selected else tickets
        results = call(lambda graph: _run_many(graph, batch))
        _invalidate_queues()
        st.subheader("Results")
        for tid, result in results.items():
            _render_run_result(tid, result)

elif page == "Test a ticket manually":
    st.title("Test a ticket manually")
    st.caption("Paste in ticket content — e.g. something that arrived from an outside inbox — and run it through the pipeline right away.")

    with st.form("manual_ticket_form"):
        ticket_id = st.text_input("Ticket ID")
        col1, col2 = st.columns(2)
        from_name = col1.text_input("From name")
        from_email = col2.text_input("From email")
        subject = st.text_input("Subject")
        body = st.text_area("Body", height=200)
        submitted = st.form_submit_button("Run")

    if submitted:
        if not all([ticket_id, from_name, from_email, subject, body]):
            st.error("All fields are required.")
        else:
            if call_db(lambda: review.ticket_exists(ticket_id)):
                st.warning(f"Ticket ID '{ticket_id}' already exists — running this will overwrite it.")

            ticket = {
                "id": ticket_id,
                "from_name": from_name,
                "from_email": from_email,
                "subject": subject,
                "body": body,
            }
            result = call(lambda graph: review.run_ticket(graph, ticket))
            _invalidate_queues()
            st.subheader("Result")
            _render_run_result(ticket_id, result)

elif page == "Escalations":
    st.title("🚨 Escalations")
    if "escalations" not in st.session_state:
        st.session_state.escalations = call(review.list_escalations)
    if st.button("🔄 Refresh"):
        st.session_state.escalations = call(review.list_escalations)

    escalations = st.session_state.escalations
    if not escalations:
        st.write("Nothing pending.")
    for esc in escalations:
        with st.container(border=True):
            st.subheader(esc["ticket_id"])
            st.caption(" · ".join(filter(None, [esc.get("category"), esc.get("reason")])))
            st.markdown(f"**From:** {esc.get('from_name')} <{esc.get('from_email')}>")
            st.markdown(f"**Subject:** {esc.get('subject')}")
            st.markdown(esc.get("body") or "")

            response = st.text_area("Response to send", key=f"resp_{esc['ticket_id']}", height=150)
            resolved_by = st.text_input("Your name/email", key=f"by_{esc['ticket_id']}")

            c1, c2 = st.columns(2)
            if c1.button("Send response", key=f"send_{esc['ticket_id']}", disabled=not response):
                call(lambda graph, tid=esc["ticket_id"]: review.resolve_escalation(graph, tid, response, resolved_by))
                _invalidate_queues()
                st.rerun()
            if c2.button("Reject / close", key=f"reject_{esc['ticket_id']}"):
                call(lambda graph, tid=esc["ticket_id"]: review.resolve_escalation(graph, tid, None, resolved_by))
                _invalidate_queues()
                st.rerun()

elif page == "Drafts for review":
    st.title("📝 Drafts for review")
    if "drafts" not in st.session_state:
        st.session_state.drafts = call(review.list_drafts)
    if st.button("🔄 Refresh"):
        st.session_state.drafts = call(review.list_drafts)

    drafts = st.session_state.drafts
    if not drafts:
        st.write("Nothing pending.")
    for d in drafts:
        with st.container(border=True):
            st.subheader(d["ticket_id"])
            st.caption(d.get("category") or "")
            st.markdown(f"**From:** {d.get('from_name')} <{d.get('from_email')}>")
            st.markdown(f"**Subject:** {d.get('subject')}")
            with st.expander("Original ticket body"):
                st.markdown(d.get("body") or "")

            edited = st.text_area(
                "Draft response", value=d.get("response_text") or "", key=f"draft_{d['ticket_id']}", height=250
            )

            c1, c2 = st.columns(2)
            if c1.button("Approve / save", key=f"approve_{d['ticket_id']}"):
                call_db(lambda tid=d["ticket_id"], text=edited: review.resolve_draft(tid, text, reject=False))
                _invalidate_queues()
                st.rerun()
            if c2.button("Reject", key=f"draft_reject_{d['ticket_id']}"):
                call_db(lambda tid=d["ticket_id"]: review.resolve_draft(tid, None, reject=True))
                _invalidate_queues()
                st.rerun()

elif page == "Auto-resolved":
    st.title("✅ Auto-resolved")
    st.caption("Read-only — these were sent automatically with no human review.")
    if "auto_resolved" not in st.session_state:
        st.session_state.auto_resolved = call(review.list_auto_resolved)
    if st.button("🔄 Refresh"):
        st.session_state.auto_resolved = call(review.list_auto_resolved)

    sent = st.session_state.auto_resolved
    if not sent:
        st.write("Nothing sent yet.")
    for s in sent:
        with st.container(border=True):
            st.subheader(s["ticket_id"])
            st.caption(s.get("category") or "")
            st.markdown(f"**From:** {s.get('from_name')} <{s.get('from_email')}>")
            st.markdown(f"**Subject:** {s.get('subject')}")
            with st.expander("Original ticket body"):
                st.markdown(s.get("body") or "")

            if s.get("response_text"):
                st.caption("Response sent")
                st.text(s["response_text"])
            else:
                st.caption("No reply was sent (e.g. spam closed with no response).")
