from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..config.postgres import postgres_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(postgres_settings.sqlalchemy_url)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def dispose_engine() -> None:
    """
    Dispose the cached engine and clear it, so the next get_engine() call
    creates a fresh one. Callers that open a new event loop per call (e.g.
    Streamlit's rerun-per-interaction model) must use this instead of
    `get_engine().dispose()` — asyncpg connections are bound to the loop
    that created them, so a disposed-but-still-cached engine would hand the
    next loop connections tied to a dead one.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
