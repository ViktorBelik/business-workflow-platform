import asyncio
from pathlib import Path

import asyncpg  # type: ignore[import-untyped]
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.infrastructure.database import get_session
from backend.app.main import app


def get_test_database_url() -> URL:
    return settings.database_url.set(database="workflow_test")


async def create_test_database() -> None:
    database_name = "workflow_test"

    if database_name != get_test_database_url().database:
        raise RuntimeError("Unexpected test database name")

    admin_url = settings.database_url.set(database="postgres")

    connection = await asyncpg.connect(
        host=admin_url.host,
        port=admin_url.port,
        user=admin_url.username,
        password=admin_url.password,
        database=admin_url.database,
    )

    try:
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            database_name,
        )

        if not exists:
            await connection.execute('CREATE DATABASE "workflow_test"')
    finally:
        await connection.close()


def migrate_test_database() -> None:
    if get_test_database_url().database != "workflow_test":
        raise RuntimeError("Unexpected test database name")

    project_root = Path(__file__).resolve().parent.parent
    alembic_config = Config(str(project_root / "alembic.ini"))

    alembic_config.attributes["database_url"] = get_test_database_url()

    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    asyncio.run(create_test_database())
    migrate_test_database()


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        get_test_database_url(),
        pool_pre_ping=True,
    )

    async with engine.connect() as connection:
        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

        await transaction.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)


if __name__ == "__main__":
    asyncio.run(create_test_database())
    migrate_test_database()
