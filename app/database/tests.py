import json

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)

from database.models import Test


async def add_tests(
    async_session: async_sessionmaker[AsyncSession],
    challenge: int,
    main_metric: str,
    main_metric_parameters: str,
    additional_metrics: str,
) -> dict:
    test_model_main = Test(
        challenge=challenge,
        metric=main_metric,
        metric_parameters=main_metric_parameters,
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
                    metric_parameters=metric["params"],
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
        "success": True,
        "test_main_metric": main_metric,
        "test_additional_metrics": additional_metrics,
        "message": "Test uploaded successfully",
    }
