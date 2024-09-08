from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from database.models import Submission


async def challenge_participants(
    async_session: async_sessionmaker[AsyncSession],
    challenge_id: int,
) -> list[int]:
    """
    Given a challenge returns the list of all participants, without repetitions.
    """
    async with async_session as session:
        submissions = (
            (
                await session.execute(
                    select(Submission).filter_by(challenge=challenge_id)
                )
            )
            .scalars()
            .all()
        )

    participants = len(set([submission.submitter for submission in submissions]))

    return participants
