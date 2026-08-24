from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ..config.postgres import postgres_settings


@asynccontextmanager
async def get_checkpointer():
    """
    Postgres-backed checkpointer for LangGraph. Persists paused runs (e.g. a
    ticket sitting at the escalate interrupt) so they survive process
    restarts and can be resumed by whatever resumes human review submits it
    to, not just the process that started the run.
    """
    async with AsyncPostgresSaver.from_conn_string(postgres_settings.psycopg_dsn) as checkpointer:
        await checkpointer.setup()
        yield checkpointer
