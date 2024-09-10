import json

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from database.models import Test


async def add_tests(
    async_session: async_sessionmaker[AsyncSession],
    challenge: int,
    main_metric: str,
    main_metric_parameters: str,
    additional_metrics: str,
) -> dict:
    """
    Adds tests for the main metric and additional metric for a given challenge.
    """
    main_metric_parameters_json = json.loads(main_metric_parameters)
    test_model_main = Test(
        challenge=challenge,
        metric=main_metric,
        metric_parameters=json.dumps(main_metric_parameters_json),
        main_metric=True,
        active=True,
    )

    if additional_metrics:
        async with async_session as session:
            session.add(test_model_main)

            metrics = json.loads(additional_metrics)
            for metric in metrics:
                test_model = Test(
                    challenge=challenge,
                    metric=metric["name"],
                    metric_parameters=json.dumps(metric["params"]),
                    main_metric=False,
                    active=True,
                )
                session.add(test_model)
            await session.commit()

    else:
        async with async_session as session:
            session.add(test_model_main)
            await session.commit()

    return {
        "test_main_metric": main_metric,
        "test_additional_metrics": additional_metrics,
    }


async def challenge_main_metric(
    async_session: async_sessionmaker[AsyncSession],
    challenge_id: int,
) -> Test:
    """
    Given a challenge returns the main metric.
    """
    async with async_session as session:
        main_test = (
            (
                await session.execute(
                    select(Test).filter_by(
                        challenge=challenge_id, main_metric=True)
                )
            )
            .scalars()
            .one()
        )

    return main_test


async def challenge_additional_metrics(
    async_session: async_sessionmaker[AsyncSession],
    challenge_id: int,
) -> list[Test]:
    """
    Given a challenge returns the list of all additional metrics (without the
    main metric).
    """
    async with async_session as session:
        additional_tests = (
            (
                await session.execute(
                    select(Test).filter_by(
                        challenge=challenge_id, main_metric=False)
                )
            )
            .scalars()
            .all()
        )

    return additional_tests
