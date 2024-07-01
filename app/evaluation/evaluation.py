import zipfile
import os
import json
import evaluation.evaluation_helper as evaluation_helper

from datetime import datetime
from fastapi import UploadFile, File, HTTPException
from sqlalchemy import select
from typing import Any
from shutil import rmtree
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from os.path import exists

from metrics.metrics import (
    metric_info,
    calculate_metric,
    all_metrics,
    calculate_default_metric,
)
from global_helper import (
    check_challenge_in_store,
    check_zip_structure,
    check_file_extension,
)
from database.models import Submission, Challenge, Test, Evaluation

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
    submitter = evaluation_helper.check_submitter(username)
    description = evaluation_helper.check_description(description)
    check_file_extension(submission_file, "tsv")

    async with async_session as session:
        challenge = (
            (await session.execute(select(Challenge).filter_by(title=challenge_title)))
            .scalars()
            .one()
        )

        tests = (
            (await session.execute(select(Test).filter_by(challenge=challenge.id)))
            .scalars()
        )

        submitter = (
            (await session.execute(select(User).filter_by(username=username)))
            .scalars()
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

    challenge_not_exist_error = not check_challenge_in_store(challenge_name)
    if challenge_not_exist_error:
        raise HTTPException(
            status_code=422,
            detail=f'Expected file for challenge "{challenge_name}" does not exist in store!',
        )

    stamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    submission = Submission(
        challenge=challenge.id,
        submitter=submitter.id,
        description=description,
        stamp=stamp,
        deleted=False,
    )
    async with async_session as session:
        session.add(submission)
        await session.commit()

    expected_file = open(
        f"{challenges_dir}/{challenge_name}.tsv",
        "r",
    )
    expected_results = [float(line) for line in expected_file.readlines()]
    submission_results = [
        float(line.strip())
        for line in (await submission_file.read()).decode("utf-8").splitlines()
    ]

    tests_evaluations = []
    for test in tests:
        tests_evaluations.append({
            "score": await evaluate(
                metric=test.metric,
                parameters=test.metric_parameters,
                out=submission_results,
                expected=expected_results,
            ),
            "test_id": test.id,
        })

    evaluations = [
        Evaluation(
            test=test_evaluation.get("test_id"),
            submission=submission.id,
            score=test_evaluation.get("score"),
            stamp=stamp,
        )
        for test_evaluation in tests_evaluations
    ]

    async with async_session as session:
        for evaluation in evaluations:
            session.add(evaluation)

        await session.commit()

    return {
        "success": True,
        "submission": "description",
        "message": "Submission added successfully",
    }


async def evaluate(metric: str, parameters: str, out: list[Any], expected: list[Any]):
    if parameters and parameters != "":
        parameters = parameters[1:-1].replace("\\", "")
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
    result = []

    async with async_session as session:
        submissions = await session.execute(
            select(Submission).filter_by(challenge=challenge)
        )
        sorting = (
            (await session.execute(select(Challenge).filter_by(title=challenge)))
            .scalars()
            .one()
            .sorting
        )

    for submission in submissions.scalars().all():
        result.append(
            {
                "id": submission.id,
                "submitter": submission.submitter,
                "description": submission.description,
                "dev_result": submission.dev_result,
                "test_result": submission.test_result,
                "timestamp": submission.timestamp,
            }
        )

    result = sorted(
        result, key=lambda d: d["test_result"], reverse=(sorting == "descending")
    )
    return result


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
    async_session: async_sessionmaker[AsyncSession], challenge: str
):
    result = []

    async with async_session as session:
        submissions = await session.execute(
            select(Submission).filter_by(challenge=challenge)
        )
        sorting = (
            (await session.execute(select(Challenge).filter_by(title=challenge)))
            .scalars()
            .one()
            .sorting
        )

    submissions = submissions.scalars().all()
    submitters = list(set([submission.submitter for submission in submissions]))

    for submitter in submitters:
        submitter_submissions = list(
            filter(lambda submission: submission.submitter == submitter, submissions)
        )
        max_test_result = max(
            [submission.test_result for submission in submitter_submissions]
        )
        best_result = list(
            filter(
                lambda submission: submission.test_result == max_test_result,
                submitter_submissions,
            )
        )[0]
        result.append(
            {
                "id": best_result.id,
                "submitter": best_result.submitter,
                "description": best_result.description,
                "dev_result": best_result.dev_result,
                "test_result": best_result.test_result,
                "timestamp": best_result.timestamp,
            }
        )

    result = sorted(
        result, key=lambda d: d["test_result"], reverse=(sorting == "descending")
    )
    return result


async def submit_test(
    username: str, description: str, challenge: Challenge, sub_file_path: str
):
    submitter = evaluation_helper.check_submitter(username)
    description = f"Create challenge {challenge.title} submission test"

    metric = challenge.main_metric
    parameters = challenge.main_metric_parameters

    dev_result = 0
    test_result = 0

    required_submission_files = ["dev-0/out.tsv", "test-A/out.tsv"]
    with zipfile.ZipFile(sub_file_path, "r") as zip_ref:
        challenge_name = zip_ref.filelist[0].filename[:-1]

        folder_name_error = not challenge.title == challenge_name
        challenge_not_exist_error = not check_challenge_in_store(challenge_name)
        structure_error = check_zip_structure(
            zip_ref, challenge_name, required_submission_files
        )

        if True not in [folder_name_error, challenge_not_exist_error, structure_error]:
            for file in zip_ref.filelist:
                if file.filename == f"{challenge_name}/dev-0/out.tsv":
                    with zip_ref.open(file, "r") as submission_out_content:
                        dev_file_from_challenge = open(
                            f"{challenges_dir}/{challenge_name}/dev-0/expected.tsv", "r"
                        )
                        challenge_results = [
                            float(line) for line in dev_file_from_challenge.readlines()
                        ]
                        submission_results = [
                            float(line) for line in submission_out_content.readlines()
                        ]
                        dev_result = await evaluate(
                            metric=metric,
                            parameters=parameters,
                            out=submission_results,
                            expected=challenge_results,
                        )

                if file.filename == f"{challenge_name}/test-A/out.tsv":
                    with zip_ref.open(file, "r") as submission_out_content:
                        test_file_from_challenge = open(
                            f"{challenges_dir}/{challenge_name}/test-A/expected.tsv",
                            "r",
                        )
                        challenge_results = [
                            float(line) for line in test_file_from_challenge.readlines()
                        ]
                        submission_results = [
                            float(line) for line in submission_out_content.readlines()
                        ]
                        test_result = await evaluate(
                            metric=metric,
                            parameters=parameters,
                            out=submission_results,
                            expected=challenge_results,
                        )

    os.remove(sub_file_path)

    if folder_name_error:
        if exists(f"{challenges_dir}/{challenge.title}"):
            rmtree(f"{challenges_dir}/{challenge.title}")
        raise HTTPException(
            status_code=422,
            detail=f'Invalid test submission folder name "{challenge_name}" - is not equal to challenge title "{challenge.title}"',
        )

    if challenge_not_exist_error:
        if exists(f"{challenges_dir}/{challenge.title}"):
            rmtree(f"{challenges_dir}/{challenge.title}")
        raise HTTPException(
            status_code=422,
            detail=f'Test submission "{challenge_name}" not exist in store!',
        )

    if structure_error:
        if exists(f"{challenges_dir}/{challenge.title}"):
            rmtree(f"{challenges_dir}/{challenge.title}")
        raise HTTPException(
            status_code=422,
            detail=f"Bad test submission structure! Test submission required files: {str(required_submission_files)}",
        )

    timestamp = datetime.now().strftime("%d-%m-%Y, %H:%M:%S")

    create_submission_model = Submission(
        challenge=challenge.title,
        submitter=submitter,
        description=description,
        dev_result=dev_result,
        test_result=test_result,
        timestamp=timestamp,
        deleted=False,
    )

    return {
        "success": True,
        "test submission": create_submission_model.description,
        "message": "Submission tested successfully",
    }
