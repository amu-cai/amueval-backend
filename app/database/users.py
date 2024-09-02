from database.models import User, Submission, Challenge

from sqlalchemy import (
    select,
    exists,
)
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from typing import Any


async def get_user_submissions(
    async_session: async_sessionmaker[AsyncSession], user_name: str
) -> list[dict[str, Any]]:
    result = []

    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=user_name)))
            .scalars()
            .one()
        )

        submissions = (
            (
                await session.execute(
                    select(Submission).filter_by(submitter=user.id, deleted=False)
                )
            )
            .scalars()
            .all()
        )

        for submission in submissions:
            challenge = (
                (await session.execute(select(Challenge).filter_by(id=submission.id)))
                .scalars()
                .one()
            )

            result.append(
                dict(
                    id=submission.id,
                    challenge=challenge.title,
                    description=submission.description,
                    timestamp=submission.timestamp,
                )
            )

    return result


async def get_user_challenges(
    async_session: async_sessionmaker[AsyncSession], user_name: str
) -> list[dict[str, Any]]:
    result = []

    async with async_session as session:
        challenges = (
            (
                await session.execute(
                    select(Challenge).filter_by(author=user_name, deleted=False)
                )
            )
            .scalars()
            .all()
        )

        for challenge in challenges:
            result.append(
                dict(
                    id=challenge.id,
                    title=challenge.title,
                    source=challenge.source,
                    type=challenge.type,
                    description=challenge.description,
                    deadline=challenge.deadline,
                    award=challenge.award,
                )
            )

    return result


async def check_user_exists(
    async_session: async_sessionmaker[AsyncSession], user_name: str
) -> bool:
    async with async_session as session:
        user_exist = (
            await session.execute(
                exists(User).where(User.username == user_name).select()
            )
        ).scalar()

    return user_exist
