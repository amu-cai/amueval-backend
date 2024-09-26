from sqlalchemy import (
    exists,
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


async def check_submission_exists(
    async_session: async_sessionmaker[AsyncSession],
    submission_id: int,
) -> bool:
    """
    Checks, if a given submission exists.
    """
    async with async_session as session:
        submission_exist = (
            await session.execute(
                exists(Submission).where(Submission.id == submission_id).select()
            )
        ).scalar()

    return submission_exist


async def get_submission(
    async_session: async_sessionmaker[AsyncSession],
    submission_id: int,
) -> Submission:
    """
    Given submission id returns the whole submission.
    """
    async with async_session as session:
        submission = (
            (await session.execute(select(Submission).filter_by(id=submission_id)))
            .scalars()
            .one()
        )

    return submission


async def delete_submissions(
    async_session: async_sessionmaker[AsyncSession],
    submissions: list[Submission],
) -> None:
    """
    Deletes the list of given submissions.
    """
    async with async_session as session:
        for submission in submissions:
            await session.delete(submission)

        await session.commit()


async def check_submission_author(
    async_session: async_sessionmaker[AsyncSession],
    submission_id: int,
    user_id: int,
) -> bool:
    """
    Checks, if given submission is created by given user.
    """
    async with async_session as session:
        submission = (
            (await session.execute(select(Submission).filter_by(id=submission_id)))
            .scalars()
            .one()
        )

        result = submission.submitter == user_id

    return result


async def edit_submission(
    async_session: async_sessionmaker[AsyncSession],
    submission_id: int,
    description: str,
) -> None:
    """
    Changes submission description.
    """
    async with async_session as session:
        submission = (
            (await session.execute(select(Submission).filter_by(id=submission_id)))
            .scalars()
            .one()
        )

        submission.description = description

        await session.commit()
