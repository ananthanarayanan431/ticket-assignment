# Take-Home: Support Concierge — Multi-Agent Ticket Triage System

## Context

You're prototyping for a client: a mid-sized SaaS company that wants to
automate first-line handling of inbound support tickets using an agentic system. This is
exploratory work ahead of a possible engagement — the client wants to see how we'd architect and
build something like this before committing budget to a full build.

## The problem

Build a multi-agent system that ingests a support ticket (subject + body text) and, for each
ticket:

1. **Classifies** the ticket's intent/category (e.g. billing question, bug report, feature
   request, account/security issue, spam, other — define your own taxonomy).
2. **Extracts** relevant structured fields (e.g. account/customer identifiers mentioned, product
   area, urgency signals, sentiment).
3. **Decides on an action**:
   - **Auto-resolve** — send a canned/templated response and close the ticket.
   - **Draft for review** — generate a personalized response, but queue it for a human to
     approve, edit, or reject before it's sent.
   - **Escalate** — route directly to a human agent with no auto-generated response (for
     sensitive, high-risk, or low-confidence cases).
4. **Logs the full decision trail** — what each agent produced, the confidence behind the
   routing decision, and the reasoning — in a way a human could audit later and understand
   *why* the system did what it did.

The client has one hard requirement: **nothing involving money (refunds, billing changes,
cancellations), account deletion, legal threats, or security reports may be auto-resolved
without a human in the loop — regardless of how confident the system is.** Getting this wrong
erodes trust in the whole product, so err on the side of caution over automation rate.

## What we're actually testing

This isn't about building a great classifier. We want to see how you **architect** a multi-agent
system: how you split responsibilities across agents, how information and control flow between
them, how you handle uncertainty and failure, and how you'd explain your decisions to both an
engineer and a client. Code volume matters much less than the quality of the reasoning behind it.

## Requirements

**1. Multi-agent architecture**
At least three agents with clearly separated responsibilities (for example: extraction /
classification, decision-making, response drafting — or a decomposition of your own choosing).
Tell us your orchestration pattern (sequential pipeline, supervisor/router, graph with
conditional edges, etc.) and why you chose it over the alternatives.

**2. Confidence-driven routing**
The auto-resolve / draft-for-review / escalate decision must be driven by an actual confidence
signal, not a fixed rule keyed only on category. Tell us where that signal comes from (model-
reported confidence, self-consistency across multiple calls, a lightweight classifier,
heuristics layered on the LLM output, etc.) and how you picked your thresholds.

**3. Human-in-the-loop**
Build a way for a human to see what's sitting in the "draft for review" and "escalate" queues
and act on it — approve / edit / reject is enough. A CLI or a couple of API endpoints is fine.
No need for a polished UI.

**4. Audit trail**
Persist every ticket's full decision trail somewhere queryable (SQLite, a JSON store, Postgres —
your call). We should be able to look at any ticket after the fact and reconstruct exactly what
happened and why.

**5. Failure handling**
LLM calls fail, time out, and return malformed output in production. Show us what your system
does when that happens to at least one agent in the pipeline. It should degrade safely (e.g.
toward escalation), not crash or silently drop the ticket.

**6. Run it against the provided sample data**
`sample_tickets.json` has 18 tickets, several of them deliberately awkward — that's the point.
Run your pipeline against all of them and include the output (a results file is fine). We're
specifically interested in how your system handles the tricky ones.

**7. Written README**
Cover:
- Your architecture (a diagram is welcome, plain text is fine)
- The key decisions you made and what you traded off
- How your system handled each of the tricky sample tickets, and why
- How you'd scale this from a demo to ~500k tickets/day — what breaks first, what changes
- How you'd evaluate and monitor agent quality over time once this is live and prompts/models
  start drifting
- What you'd do differently with another week

## Explicitly your choice

- **Framework** — LangGraph, or any another orchestration framework
- **LLM** 
- **Stack** — Python or TypeScript, whatever you're most productive in.
- **AI coding assistants** — using Claude, Copilot, etc. is expected and fine. We care about the
  decisions behind the code, not whether every line was hand-typed.

  Choice of framework and llm used must be justified.

## Explicitly out of scope

- Real email ingestion — reading from the provided JSON file is fine.
- A polished frontend for the human-review queue.
- Deployment/infra (a Dockerfile is a nice-to-have, not required).

## Bonus / stretch goals (entirely optional)

- A reflection/self-critique step where a review agent double-checks a drafted response before
  it's queued for human approval.
- A small eval harness that scores your system's routing decisions against a labeled subset of
  the sample tickets, so regressions in prompts/logic are visible before they ship.

## Time

We'd expect focused work of around **4–6 hours**. Please don't spend more than **8** — we're
evaluating judgment and architecture, not endurance. If you run out of time, tell us in the
README what you'd have done next rather than leaving it unsaid.

## Submission

A repo or zip with your code, the results of running it on the sample tickets, and the README.