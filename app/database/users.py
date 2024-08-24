from database.models import User, Submission, Challenge

from sqlalchemy import (
    select,
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
