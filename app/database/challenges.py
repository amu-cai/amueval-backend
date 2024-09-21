from sqlalchemy import (
    exists,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from typing import Any

from database.models import Challenge


async def add_challenge(
    async_session: async_sessionmaker[AsyncSession],
    user_name: str,
    title: str,
    source: str,
    description: str,
    type: str,
    deadline: str,
    award: str,
) -> dict[str, Any]:
    """
    Adds challenge to the table.
    """
    challenge = Challenge(
        author=user_name,
        title=title,
        type=type,
        source=source,
        description=description,
        deadline=deadline,
        award=award,
        deleted=False,
    )

    async with async_session as session:
        session.add(challenge)

        await session.flush()

        challenge_id = challenge.id
        challenge_title = challenge.title

        await session.commit()

    return {
        "challenge_title": challenge_title,
        "challenge_id": challenge_id,
    }


async def check_challenge_exists(
    async_session: async_sessionmaker[AsyncSession],
    title: str,
) -> bool:
    """
    Checks, if a given chellenge exists.
    """
    async with async_session as session:
        challenge_exist = (
            await session.execute(
                exists(Challenge).where(Challenge.title == title).select()
            )
        ).scalar()

    return challenge_exist


async def check_challenge_author(
    async_session: async_sessionmaker[AsyncSession],
    challenge_title: str,
    user_name: str,
) -> bool:
    """
    Checks, if given challenge is created by given user.
    """
    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge_title)))
            .scalars()
            .one()
        )

        result = challenge.author == user_name

    return result


async def edit_challenge(
    async_session: async_sessionmaker[AsyncSession],
    title: str,
    description: str,
    deadline: str,
) -> None:
    """
    Changes challange description and deadline.
    """
    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=title)))
            .scalars()
            .one()
        )

        challenge.deadline = deadline
        challenge.description = description

        await session.commit()


async def all_challenges(
    async_session: async_sessionmaker[AsyncSession],
) -> list[Challenge]:
    """
    Returns list of all challenges.
    """
    async with async_session as session:
        challenges = (
            (await session.execute(select(Challenge).filter_by(deleted=False)))
            .scalars()
            .all()
        )

    return challenges


async def get_challenge(
    async_session: async_sessionmaker[AsyncSession],
    title: str,
) -> Challenge:
    """
    Given challenge title returns the challenge.
    """
    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=title)))
            .scalars()
            .one()
        )
        return challenge
