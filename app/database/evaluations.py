from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm.exc import NoResultFound

from database.models import Evaluation


async def test_best_score(
    async_session: async_sessionmaker[AsyncSession],
    test_id: int,
    sorting: str,
) -> float | None:
    """
    Given a test returns the best score for the test.
    """
    evaluations = await test_evaluations(
        async_session=async_session,
        test_id=test_id,
    )

    if not evaluations:
        return None

    sorted_scores = sorted(
        evaluations, key=lambda x: x.score, reverse=(sorting != "descending")
    )

    best_score = sorted_scores[0].score
    return best_score


async def test_evaluations(
    async_session: async_sessionmaker[AsyncSession],
    test_id: int,
) -> list[Evaluation]:
    """
    Given a test returns the list of all evaluations.
    """
    try:
        async with async_session as session:
            evaluations = (
                (await session.execute(select(Evaluation).filter_by(test=test_id)))
                .scalars()
                .all()
            )

        return evaluations
    except NoResultFound:
        return []


async def add_evaluation(
    async_session: async_sessionmaker[AsyncSession],
    test: int,
    submission: int,
    score: float,
    timestamp: str,
) -> int:
    """
    Adds evaluation to the table.
    """
    evaluation = Evaluation(
        test=test,
        submission=submission,
        score=score,
        timestamp=timestamp,
    )

    async with async_session as session:
        session.add(evaluation)

        await session.flush()

        evaluation_id = evaluation.id

        await session.commit()

    return evaluation_id


async def submission_evaluations(
    async_session: async_sessionmaker[AsyncSession],
    submission_id: int,
) -> list[Evaluation]:
    """
    Given submission id returns a list of all evaluations associated with it.
    """
    async with async_session as session:
        evaluations = (
            (
                await session.execute(
                    select(Evaluation).filter_by(submission=submission_id)
                )
            )
            .scalars()
            .all()
        )

    return evaluations
