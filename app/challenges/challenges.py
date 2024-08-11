import os

from database.models import Challenge, Test, Evaluation, Submission, User

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

            submissions = (
                (
                    await session.execute(
                        select(Submission).filter_by(challenge=challenge.id)
                    )
                )
                .scalars()
                .all()
            )

            participants = len(
                set([submission.submitter for submission in submissions])
            )

            try:
                scores = (
                    await session.execute(select(Evaluation).filter_by(test=test.id))
                ).scalars()
                sorted_scores = sorted(scores, key=lambda x: x.score)
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
                    "main_metric": test.metric,
                    "best_sore": best_score,
                    "deadline": challenge.deadline,
                    "award": challenge.award,
                    "deleted": challenge.deleted,
                    # TODO: change to sorting from the metric
                    "sorting": "descending",
                    "participants": participants,
                }
            )
        else:
            result.append(
                {
                    "id": challenge.id,
                    "title": challenge.title,
                    "type": challenge.type,
                    "description": challenge.description,
                    "main_metric": test.metric,
                    "best_sore": "No best score yet",
                    "deadline": challenge.deadline,
                    "award": challenge.award,
                    "deleted": challenge.deleted,
                    # TODO: change to sorting from the metric
                    "sorting": "descending",
                    "participants": participants,
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

        tests = (
            (await session.execute(select(Test).filter_by(challenge=challenge.id)))
            .scalars()
            .all()
        )

        main_test = next(filter(lambda x: x.main_metric, tests))

        additional_metrics = [test.metric for test in tests if not test.main_metric]

        submissions = (
            (
                await session.execute(
                    select(Submission).filter_by(challenge=challenge.id)
                )
            )
            .scalars()
            .all()
        )

        participants = len(set([submission.submitter for submission in submissions]))

        sorted_evaluations = (
            (await session.execute(select(Evaluation).filter_by(test=main_test.id)))
            .scalars()
            .all()
        ).sort(key=lambda x: x.score, reverse=True)

    best_score = sorted_evaluations[0] if sorted_evaluations else None

    return {
        "id": challenge.id,
        "title": challenge.title,
        "author": challenge.author,
        "type": challenge.type,
        "mainMetric": main_test.metric,
        "mainMetricParameters": main_test.metric_parameters,
        "description": challenge.description,
        "source": challenge.source,
        "bestScore": best_score,
        "deadline": challenge.deadline,
        "award": challenge.award,
        "deleted": challenge.deleted,
        # TODO: change to sorting from the metric
        "sorting": "descending",
        "participants": participants,
        "additional_metrics": additional_metrics,
    }


async def check_challenge_user(
    async_session: async_sessionmaker[AsyncSession],
    challenge_title: str,
    user_name: str,
) -> bool:
    async with async_sessionmaker as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge_title)))
            .scalars()
            .one()
        )

        user = (
            (await session.execute(select(User).filter_by(username=user_name)))
            .scalars()
            .one()
        )

        result = challenge.author == user.id

    return result


async def edit_challenge(
    async_session: async_sessionmaker[AsyncSession],
    challenge_title: str,
    deadline: str,
    description: str,
) -> dict:
    async with async_sessionmaker as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge_title)))
            .scalars()
            .one()
        )

        challenge.deadline = deadline
        challenge.description = description

    return dict(success=True, message=f"Challenge {challenge_title} updated")
