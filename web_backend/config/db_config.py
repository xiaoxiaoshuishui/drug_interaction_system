from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/FastAPI"
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True, pool_size=5, max_overflow=10)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()