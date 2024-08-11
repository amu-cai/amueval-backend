from sqlalchemy import (
    select,
)
from database.models import User
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from admin.models import UserRightsModel
from database.models import Challenge
from secrets import token_hex
import shutil
import os


STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

SAVE_SEPARATOR = "_~~~_"
challenges_dir = f"{STORE}/challenges"
deleted_challenges_dir = f"{STORE}/deleted_challenges"


async def get_users_settings(async_session):
    async with async_session as session:
        users = (await session.execute(select(User))).scalars().all()
    result = []
    for user in users:
        result.append(
            {
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_author": user.is_author,
            }
        )
    return result


async def user_rights_update(
    async_session: async_sessionmaker[AsyncSession], user_rights: UserRightsModel
):
    is_admin = user_rights.is_admin
    is_author = user_rights.is_author
    user_to_update = user_rights.username
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=user_to_update)))
            .scalars()
            .one()
        )
        user.is_admin = is_admin
        user.is_author = is_author
        await session.commit()
    return {
        "success": True,
        "user": user_to_update,
        "message": "User rights uploaded successfully",
    }


async def delete_challenge(
    async_session: async_sessionmaker[AsyncSession], challenge_title: str
):
    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge_title)))
            .scalars()
            .one()
        )

        challenge.deleted = True

        await session.commit()

    return dict(
        success=True,
        challenge=challenge_title,
        message="Challenge deleted",
    )
