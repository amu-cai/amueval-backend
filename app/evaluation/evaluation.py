import os
import json

from datetime import datetime
from fastapi import UploadFile, File, HTTPException
from sqlalchemy import select
from typing import Any
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)

from metrics.metrics import (
    metric_info,
    calculate_metric,
    all_metrics,
    calculate_default_metric,
)
from global_helper import (
    check_file_extension,
)
from database.models import Submission, Challenge, Test, Evaluation, User

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"


async def submit(
    async_session: async_sessionmaker[AsyncSession],
    username: str,
    description: str,
    challenge_title: str,
    submission_file: UploadFile = File(...),
):
    submitter = username
    check_file_extension(submission_file, "tsv")

    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge_title)))
            .scalars()
            .first()
        )

        tests = (
            (await session.execute(select(Test).filter_by(challenge=challenge.id)))
            .scalars()
            .all()
        )

        submitter = (
            (await session.execute(select(User).filter_by(username=username)))
            .scalars()
            .first()
        )

    challenge_name = challenge.title

    if challenge.deadline != "":
        if (
            datetime.strptime(challenge.deadline[:19], "%Y-%m-%dT%H:%M:%S")
            < datetime.now()
        ):
            raise HTTPException(
                status_code=422,
                detail="Deadline for submissions to the challenge has passed",
            )

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    expected_file = open(
        f"{challenges_dir}/{challenge_name}.tsv",
        "r",
    )
    expected_results = [float(line) for line in expected_file.readlines()]

    submission_results = [
        float(line.strip())
        for line in (await submission_file.read()).decode("utf-8").splitlines()
    ]

    async with async_session as session:
        submission = Submission(
            challenge=challenge.id,
            submitter=submitter.id,
            description=description,
            timestamp=timestamp,
            deleted=False,
        )
        session.add(submission)
        await session.flush()

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

        evaluations = [
            Evaluation(
                test=test_evaluation.get("test_id"),
                submission=submission.id,
                score=test_evaluation.get("score"),
                timestamp=timestamp,
            )
            for test_evaluation in tests_evaluations
        ]

        for evaluation in evaluations:
            session.add(evaluation)

        await session.commit()

    return {
        "success": True,
        "submission": "description",
        "message": "Submission added successfully",
    }


async def evaluate(metric: str, parameters: str, out: list[Any], expected: list[Any]):
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


async def get_metrics():
    result = [
        {
            "name": m,
            "parameters": metric_info(m)["parameters"],
            "link": metric_info(m)["link"],
        }
        for m in all_metrics()
    ]
    return result


async def get_all_submissions(
    async_session: async_sessionmaker[AsyncSession], challenge: str
):
    results = []
    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge)))
            .scalars()
            .first()
        )

        tests = (
            (await session.execute(select(Test).filter_by(challenge=challenge.id)))
            .scalars()
            .all()
        )

        main_metric_test = next(filter(lambda x: x.main_metric is True, tests))
        additional_metrics_tests = [
            test for test in tests if not test.main_metric]

        submissions = (
            (
                await session.execute(
                    select(Submission).filter_by(challenge=challenge.id)
                )
            )
            .scalars()
            .all()
        )

        for submission in submissions:
            evaluations_all = (
                (
                    await session.execute(
                        select(Evaluation).filter_by(submission=submission.id)
                    )
                )
                .scalars()
                .all()
            )

            evaluation_main_metric = next(
                filter(lambda x: x.test == main_metric_test.id, evaluations_all)
            )

            evaluations_additional_metrics = []
            for evaluation in evaluations_all:
                additional_test = next(
                    (
                        test
                        for test in additional_metrics_tests
                        if test.id == evaluation.test
                    ),
                    None,
                )
                if additional_test is not None:
                    evaluations_additional_metrics.append(
                        dict(
                            name=additional_test.metric,
                            score=evaluation.score,
                        )
                    )

            if evaluation_main_metric is not None:
                results.append(
                    dict(
                        id=submission.id,
                        submitter=submission.submitter,
                        description=submission.description,
                        timestamp=submission.timestamp,
                        main_metric_result=evaluation_main_metric.score,
                        additional_metrics_results=evaluations_additional_metrics,
                    )
                )

    sorted_result = sorted(
        results,
        key=lambda d: d["main_metric_result"],
        # TODO: change to sorting from the metric
        reverse=("descending"),
    )

    return sorted_result


async def get_my_submissions(
    async_session: async_sessionmaker[AsyncSession], challenge: str, user
):
    result = []

    async with async_session as session:
        submissions = await session.execute(
            select(Submission).filter_by(
                challenge=challenge, submitter=user["username"]
            )
        )

    for submission in submissions.scalars().all():
        result.append(
            {
                "id": submission.id,
                "description": submission.description,
                "dev_result": submission.dev_result,
                "test_result": submission.test_result,
                "timestamp": submission.timestamp,
            }
        )

    return result


async def get_leaderboard(
    async_session: async_sessionmaker[AsyncSession], challenge_name: str
):
    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge_name)))
            .scalars()
            .first()
        )

        test = (
            (
                await session.execute(
                    select(Test).filter_by(
                        challenge=challenge.id, main_metric=True)
                )
            )
            .scalars()
            .first()
        )

        evaluations = (
            (await session.execute(select(Evaluation).filter_by(test=test.id)))
            .scalars()
            .all()
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

    # TODO: change to sorting from the metric
    sorting = "ascending"
    submitters = list(
        set([submission.submitter for submission in submissions]))

    result = []
    for submitter in submitters:
        submitter_submissions = [
            submission.id
            for submission in submissions
            if submission.submitter == submitter
        ]

        sorted_submitter_evaluations = sorted(
            [
                evaluation
                for evaluation in evaluations
                if evaluation.submission in submitter_submissions
            ],
            key=lambda x: x.score,
            reverse=True,
        )

        if sorted_submitter_evaluations:
            best_result_evaluation = sorted_submitter_evaluations[0]
            best_result_submission = next(
                submission
                for submission in submissions
                if submission.id == best_result_evaluation.submission
            )

            result.append(
                {
                    "id": best_result_evaluation.submission,
                    "submitter": submitter,
                    "description": best_result_submission.description,
                    "main_metric_result": best_result_evaluation.score,
                    "timestamp": best_result_submission.timestamp,
                }
            )

    result = sorted(
        result, key=lambda d: d["main_metric_result"], reverse=(sorting == "ascending")
    )

    return result
