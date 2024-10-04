from sqlalchemy import (
    select,
    exists,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from typing import Any

from database.models import User, Submission, Challenge
from database.submissions import challenge_participants_ids
from database.tests import (
    challenge_main_metric,
)


async def get_user(
    async_session: async_sessionmaker[AsyncSession],
    user_name: str,
) -> User:
    """
    Returns @User given user name.
    """
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=user_name)))
            .scalars()
            .one()
        )

    return user


async def user_name(
    async_session: async_sessionmaker[AsyncSession],
    user_id: int,
) -> str:
    """
    Given user id returns user name.
    """
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(id=user_id))).scalars().one()
        )

    return user.username


async def get_user_submissions(
    async_session: async_sessionmaker[AsyncSession],
    user_name: str,
    challenge_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Returns list of all user submissions, given user name.
    If challenge name is given, then it returns user submissions for the
    challenge only.
    """
    result = []

    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=user_name)))
            .scalars()
            .one()
        )

        if challenge_id is None:
            submissions = (
                (
                    await session.execute(
                        select(Submission).filter_by(submitter=user.id, deleted=False)
                    )
                )
                .scalars()
                .all()
            )
        else:
            submissions = (
                (
                    await session.execute(
                        select(Submission).filter_by(
                            submitter=user.id,
                            challenge=challenge_id,
                            deleted=False,
                        )
                    )
                )
                .scalars()
                .all()
            )

        for submission in submissions:
            challenge = (
                (await session.execute(select(Challenge).filter_by(id=submission.challenge)))
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
    async_session: async_sessionmaker[AsyncSession],
    user_name: str,
) -> list[dict[str, Any]]:
    """
    Returns list of all user challenges, given user name.
    """
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
        main_test = await challenge_main_metric(
            async_session=async_session,
            challenge_id=challenge.id,
        )
        participants_number = len(
            await challenge_participants_ids(
                async_session=async_session,
                challenge_id=challenge.id,
            )
        )
        result.append(
            dict(
                id=challenge.id,
                title=challenge.title,
                source=challenge.source,
                type=challenge.type,
                description=challenge.description,
                deadline=challenge.deadline,
                award=challenge.award,
                main_metric=main_test.metric,
                participants=participants_number,
            )
        )

    return result


async def check_user_exists(
    async_session: async_sessionmaker[AsyncSession],
    user_name: str,
) -> bool:
    """
    Checks, if a given user exists.
    """
    async with async_session as session:
        user_exist = (
            await session.execute(
                exists(User).where(User.username == user_name).select()
            )
        ).scalar()

    return user_exist


async def check_user_is_admin(
    async_session: async_sessionmaker[AsyncSession],
    user_name: str,
):
    """
    Checks, if a given user has admin rights.
    """
    async with async_session as session:
        # TODO: change the request in order to take only one column
        user = (
            (await session.execute(select(User).filter_by(username=user_name)))
            .scalars()
            .one()
        )

        user_is_admin = user.is_admin

    return user_is_admin


async def challenge_participants_names(
    async_session: async_sessionmaker[AsyncSession],
    challenge_id: int,
) -> list[str]:
    """
    Given a challenge returns the number of participants, without repetitions.
    """
    users_ids = await challenge_participants_ids(
        async_session=async_session,
        challenge_id=challenge_id,
    )

    async with async_session as session:
        users_names = [
            (await session.execute(select(User).filter_by(id=user_id)))
            .scalars()
            .one()
            .username
            for user_id in users_ids
        ]

    return users_names
