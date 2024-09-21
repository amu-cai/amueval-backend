from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from database.models import Submission


async def challenge_participants_ids(
    async_session: async_sessionmaker[AsyncSession],
    challenge_id: int,
) -> list[int]:
    """
    Given a challenge returns the list of all participants ids, without repetitions.
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

    participants = set([submission.submitter for submission in submissions])

    return participants


async def add_submission(
    async_session: async_sessionmaker[AsyncSession],
    challenge: int,
    submitter: int,
    description: str,
    timestamp: str,
) -> int:
    """
    Adds submission to the submission table.
    """
    submission = Submission(
        challenge=challenge,
        submitter=submitter,
        description=description,
        timestamp=timestamp,
        deleted=False,
    )

    async with async_session as session:
        session.add(submission)

        await session.flush()

        submission_id = submission.id

        await session.commit()

    return submission_id


async def challenge_submissions(
    async_session: async_sessionmaker[AsyncSession],
    challenge_id: int,
) -> list[Submission]:
    """
    Returns a list of all submissions for a given challenge id.
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

    return submissions
