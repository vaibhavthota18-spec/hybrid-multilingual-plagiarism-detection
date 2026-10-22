"""
Async Database Session Factory and Dependency Injection
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from plagiarism.core.config import get_settings

_engine = None
_sessionmaker = None


def get_engine():
    """Returns singleton async database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DEBUG,
            future=True
        )
    return _engine


def get_session_factory():
    """Returns singleton sessionmaker."""
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine()
        _sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return _sessionmaker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session with automatic transaction management."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_health() -> bool:
    """Executes a fast ping query to verify database connectivity."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def close_db_connection() -> None:
    """Disposes of the singleton async engine connection pool on shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


class _EngineProxy:
    """Lazy proxy allowing module-level 'engine' import while deferring engine creation."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)

    async def dispose(self):
        await close_db_connection()


engine = _EngineProxy()
