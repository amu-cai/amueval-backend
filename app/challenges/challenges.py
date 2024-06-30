from database.models import Challenge
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import (
    select,
)
import os

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"


async def all_challenges(
    async_session: async_sessionmaker[AsyncSession],
) -> list[Challenge]:
    async with async_session as session:
        challenges = await session.execute(select(Challenge))
    result = []
    for challenge in challenges.scalars().all():
        result.append(
            {
                "id": challenge.id,
                "title": challenge.title,
                "type": challenge.type,
                "description": challenge.description,
                "mainMetric": challenge.main_metric,
                "bestScore": challenge.best_score,
                "deadline": challenge.deadline,
                "award": challenge.award,
                "deleted": challenge.deleted,
                "sorting": challenge.sorting,
            }
        )
    return result


async def get_challenge_info(async_session, challenge: str):
    async with async_session as session:
        challenge_info = (
            (await session.execute(select(Challenge).filter_by(title=challenge)))
            .scalars()
            .one()
        )
    return {
        "id": challenge_info.id,
        "title": challenge_info.title,
        "author": challenge_info.author,
        "type": challenge_info.type,
        "mainMetric": challenge_info.main_metric,
        "mainMetricParameters": challenge_info.main_metric_parameters,
        "description": challenge_info.description,
        "readme": challenge_info.readme,
        "source": challenge_info.source,
        "bestScore": challenge_info.best_score,
        "deadline": challenge_info.deadline,
        "award": challenge_info.award,
        "deleted": challenge_info.deleted,
        "sorting": challenge_info.sorting,
    }
