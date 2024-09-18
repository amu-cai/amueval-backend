import json
import os

from datetime import datetime
from fastapi import (
    HTTPException,
    UploadFile,
)
from pathlib import Path
from pydantic import (
    BaseModel,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from typing import Any

from database.challenges import (
    get_challenge,
)
from database.evaluations import (
    add_evaluation,
)
from database.submissions import (
    add_submission,
)
from database.tests import (
    challenge_all_tests,
)
from database.users import (
    get_user,
    check_user_exists,
)
from metrics.metrics import (
    Metrics,
    metric_info,
    calculate_metric,
    all_metrics,
    calculate_default_metric,
)

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"


class CreateSubmissionRequest(BaseModel):
    author: str
    challenge_title: str
    description: str


class MetricInfo(BaseModel):
    name: str
    parameters: list[dict[str, str]]
    link: str


async def create_submission_handler(
    async_session: async_sessionmaker[AsyncSession],
    request: CreateSubmissionRequest,
    file: UploadFile,
):
    # Checking user
    author_exists = await check_user_exists(
        async_session=async_session, user_name=request.author
    )
    if not author_exists:
        raise HTTPException(status_code=401, detail="User does not exist")

    # Checking file name
    proper_file_extension = ".tsv" == Path(file.filename).suffix
    if not proper_file_extension:
        raise HTTPException(
            status_code=415,
            detail=f"File <{file.filename}> is not a TSV file",
        )

    challenge = await get_challenge(
        async_session=async_session,
        title=request.challenge_title,
    )

    # Checking the deadline
    if challenge.deadline != "":
        if (
            datetime.strptime(challenge.deadline[:19], "%Y-%m-%dT%H:%M:%S")
            < datetime.now()
        ):
            raise HTTPException(
                status_code=403,
                detail="Submission after deadline",
            )

    expected_file = open(
        f"{challenges_dir}/{challenge.title}.tsv",
        "r",
    ).readlines()

    try:
        expected_results = [float(line) for line in expected_file]

        submission_results = [
            float(line) for line in (await file.read()).decode("utf-8").splitlines()
        ]
    except ValueError:
        expected_results = [line.strip() for line in expected_file]

        submission_results = [
            line.strip() for line in (await file.read()).decode("utf-8").splitlines()
        ]

    submitter = await get_user(
        async_session=async_session,
        user_name=request.author,
    )

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    submission = await add_submission(
        async_session=async_session,
        challenge=challenge.id,
        submitter=submitter.id,
        description=request.description,
        timestamp=timestamp,
    )

    tests = await challenge_all_tests(
        async_session=async_session,
        challenge_id=challenge.id,
    )

    tests_evaluations = []
    for test in tests:
        tests_evaluations.append(
            {
                "score": await evaluate(
                    metric=test.metric,
                    parameters=test.metric_parameters,
                    out=submission_results,
                    expected=expected_results,
                ),
                "test_id": test.id,
            }
        )

    for test_evaluation in tests_evaluations:
        await add_evaluation(
            async_session=async_session,
            test=test_evaluation.get("test_id"),
            submission=submission,
            score=test_evaluation.get("score"),
            timestamp=timestamp,
        )

    return {
        "success": True,
        "submission": "description",
        "message": "Submission added successfully",
    }


async def evaluate(
    metric: str, parameters: str, out: list[Any], expected: list[Any]
) -> float:
    """
    Evaluates the metric with given parameters.
    """
    if parameters and parameters != "{}":
        params_dict = json.loads(parameters)
        result = calculate_metric(
            metric_name=metric, expected=expected, out=out, params=params_dict
        )
    else:
        result = calculate_default_metric(
            metric_name=metric, expected=expected, out=out
        )

    return result


async def get_metrics_handler() -> list[MetricInfo]:
    result = [
        MetricInfo(
            name=m,
            parameters=metric_info(m)["parameters"],
            link=metric_info(m)["link"],
        )
        for m in all_metrics()
    ]
    return result
