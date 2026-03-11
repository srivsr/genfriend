import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Initialize database.

    In DEVELOPMENT: Creates tables automatically (convenient for testing)
    In PRODUCTION: Only verifies connection (use Alembic migrations for schema changes)

    To disable auto-creation, set AUTO_CREATE_TABLES=false in .env
    """
    if settings.is_production:
        logger.info("Production mode: Skipping auto table creation. Use 'alembic upgrade head' for migrations.")
        # Just verify connection works
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified.")
        return

    if settings.auto_create_tables:
        logger.info("Development mode: Auto-creating tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created/verified.")
    else:
        logger.info("Auto table creation disabled. Use 'alembic upgrade head' for migrations.")
