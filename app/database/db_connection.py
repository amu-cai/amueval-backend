from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

import os

DB_NAME_ENV = os.getenv("DB_NAME")
if DB_NAME_ENV is not None:
    DB_NAME = DB_NAME_ENV
else:
    raise FileNotFoundError("DB_NAME env variable not defined")

DB_USER_ENV = os.getenv("DB_USER")
if DB_USER_ENV is not None:
    DB_USER = DB_USER_ENV
else:
    raise FileNotFoundError("DB_USER env variable not defined")

DB_PASS_ENV = os.getenv("DB_PASS")
if DB_PASS_ENV is not None:
    DB_PASS = DB_PASS_ENV
else:
    raise FileNotFoundError("DB_PASS env variable not defined")

DB_HOST_ENV = os.getenv("DB_HOST")
if DB_HOST_ENV is not None:
    DB_HOST = DB_HOST_ENV
else:
    raise FileNotFoundError("DB_HOST env variable not defined")

DB_PORT_ENV = os.getenv("DB_PORT")
if DB_PORT_ENV is not None:
    DB_PORT = DB_PORT_ENV
else:
    raise FileNotFoundError("DB_PORT env variable not defined")

DB_CONNECTION_URL = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
    DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
)


def get_engine() -> AsyncEngine:
    engine = create_async_engine(
        DB_CONNECTION_URL,
        echo=True,
    )
    return engine


def get_session(engine: AsyncEngine) -> AsyncSession:
    async_session = async_sessionmaker(engine, expire_on_commit=True)
    return async_session
