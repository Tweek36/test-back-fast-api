from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


DATABASE_URL = "postgresql+asyncpg://postgres:admin@127.0.0.1:5432/tests"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
)

async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session