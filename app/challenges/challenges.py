import os

from database.models import Challenge, Test, Evaluation

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import (
    select,
)
from sqlalchemy.orm.exc import NoResultFound

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
        challenges = (await session.execute(select(Challenge))).scalars().all()

    result = []
    for challenge in challenges:
        async with async_session as session:
            test = (
                (
                    await session.execute(
                        select(Test).filter_by(challenge=challenge.id, main_metric=True)
                    )
                )
                .scalars()
                .one()
            )

            try:
                scores = (
                    (await session.execute(select(Evaluation).filter_by(test=test.id)))
                    .scalars()
                )
                sorted_scores = sorted(scores, key=lambda x: x["score"])
                best_score = sorted_scores[0] if sorted_scores else None
            except NoResultFound:
                best_score = None

        if best_score is not None:
            result.append(
                {
                    "id": challenge.id,
                    "title": challenge.title,
                    "type": challenge.type,
                    "description": challenge.description,
                    "main_metric": test.main_metric,
                    "best_sore": best_score,
                    "deadline": challenge.deadline,
                    "award": challenge.award,
                    "deleted": challenge.deleted,
                    "sorting": challenge.sorting,
                }
            )
        else:
            result.append(
                {
                    "id": challenge.id,
                    "title": challenge.title,
                    "type": challenge.type,
                    "description": challenge.description,
                    "main_metric": test.main_metric,
                    "best_sore": "No best score yet",
                    "deadline": challenge.deadline,
                    "award": challenge.award,
                    "deleted": challenge.deleted,
                    "sorting": challenge.sorting,
                }
            )

    return result


async def get_challenge_info(async_session, challenge: str):
    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge)))
            .scalars()
            .one()
        )

        test = (
            (
                await session.execute(
                    select(Test).filter_by(challenge=challenge.id, main_metric=True)
                )
            )
            .scalars()
            .one()
        )

        sorted_evaluations = (
            (await session.execute(select(Evaluation).filter_by(test=test.id)))
            .scalars()
            .all()
        ).sort(key=lambda x: x.score, reverse=True)

    best_score = sorted_evaluations[0] if sorted_evaluations else None

    return {
        "id": challenge.id,
        "title": challenge.title,
        "author": challenge.author,
        "type": challenge.type,
        "mainMetric": test.metric,
        "mainMetricParameters": test.metric_parameters,
        "description": challenge.description,
        "readme": challenge.readme,
        "source": challenge.source,
        "bestScore": best_score,
        "deadline": challenge.deadline,
        "award": challenge.award,
        "deleted": challenge.deleted,
        "sorting": challenge.sorting,
    }
