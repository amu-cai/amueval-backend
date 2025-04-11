import json
import os
import asyncio

from datetime import datetime
from fastapi import (
    HTTPException,
    UploadFile,
)
from pathlib import Path
from pydantic import (
    BaseModel,
    Field,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from typing import Any, Optional

from database.challenges import (
    check_challenge_exists,
    get_challenge,
)
from database.evaluations import (
    add_evaluation,
    delete_evaluations,
    submission_evaluations,
    test_evaluations,
)
from database.submissions import (
    add_submission,
    challenge_submissions,
    check_submission_author,
    check_submission_exists,
    delete_submissions,
    edit_submission,
    get_submission,
)
from database.tests import (
    challenge_all_tests,
    challenge_main_metric,
)
from database.users import (
    get_user,
    get_user_submissions,
    check_user_exists,
    check_user_is_admin,
    get_user_name,
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
    description: str = Field(max_length=25)


class MetricInfo(BaseModel):
    name: str
    parameters: list[dict[str, str]]
    link: str


class SubmissionInfo(BaseModel):
    id: int
    submitter: str
    description: str
    timestamp: str
    main_metric_result: float
    additional_metrics_results: list[dict[str, Any]] | None
    place: Optional[int] = None


async def run_evaluations(tests, submission_results, expected_results):
    tasks = [
        evaluate(
            metric=test.metric,
            parameters=test.metric_parameters,
            out=submission_results,
            expected=expected_results,
        )
        for test in tests
    ]

    scores = await asyncio.gather(*tasks)  # Run all evaluations in parallel

    # Attach scores to their corresponding test IDs
    return [{"score": score, "test_id": test.id} for score, test in zip(scores, tests)]


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

    if len(expected_results) != len(submission_results):
        raise HTTPException(
            status_code=422,
            detail="Submission file has different length than expected file",
        )

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

    tests_evaluations = await run_evaluations(tests, submission_results, expected_results)

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
    Evaluates the metric with given parameters asynchronously.
    """
    if parameters and parameters != "{}":
        params_dict = json.loads(parameters)
        result = await asyncio.to_thread(
            calculate_metric, metric, expected, out, params_dict
        )
    else:
        result = await asyncio.to_thread(
            calculate_default_metric, metric, expected, out
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


async def challenge_submissions_handler(
        async_session: async_sessionmaker[AsyncSession],
        challenge_title: str,
        user_name: str | None = None,
) -> list[SubmissionInfo]:
    """
    Given title of a challenge returns a list of all submissions, where the
    list is sorted according to the main metric.
    If user is given, then it returns user submissions for the challenge.
    """
    # Checking challenge
    challenge_exists = await check_challenge_exists(
        async_session=async_session,
        title=challenge_title,
    )
    if not challenge_exists:
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title {
        challenge_title} does
        not exist
        ",
    )

    if user_name is not None:
    # Checking user
        user_exists = await check_user_exists(
    async_session = async_session,
    user_name = user_name,

)
if not user_exists:
    raise HTTPException(status_code=401, detail="User does not exist")

challenge = await get_challenge(
    async_session=async_session,
    title=challenge_title,
)

tests = await challenge_all_tests(
    async_session=async_session,
    challenge_id=challenge.id,
)
main_metric_test = next(filter(lambda x: x.main_metric is True, tests))
additional_metrics_tests = [test for test in tests if not test.main_metric]

if user_name is None:
    submissions_full = await challenge_submissions(
        async_session=async_session,
        challenge_id=challenge.id,
    )
    submissions = [
        dict(
            id=submission.id,
            challenge=challenge.title,
            description=submission.description,
            timestamp=submission.timestamp,
            submitter=submission.submitter,
        )
        for submission in submissions_full
    ]
else:
    submissions = await get_user_submissions(
        async_session=async_session,
        user_name=user_name,
        challenge_id=challenge.id,
    )

results = []
for submission in submissions:
    all_evaluations = await submission_evaluations(
        async_session=async_session,
        submission_id=submission.get("id"),
    )
    main_metric_evaluation = next(
        (evaluation for evaluation in all_evaluations if evaluation.test == main_metric_test.id), None
    )
    # main_metric_evaluation = next(
    #     filter(lambda x: x.test == main_metric_test.id, all_evaluations)
    # )

    evaluations_additional_metrics = []
    for evaluation in all_evaluations:
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

    if main_metric_evaluation is not None:
        if user_name is None:
            submitter_name = await get_user_name(
                async_session=async_session,
                user_id=submission.get("submitter"),
            )
        else:
            submitter_name = user_name

        results.append(
            SubmissionInfo(
                id=submission.get("id"),
                submitter=submitter_name,
                description=submission.get("description"),
                timestamp=submission.get("timestamp"),
                main_metric_result=main_metric_evaluation.score,
                additional_metrics_results=evaluations_additional_metrics,
            )
        )

main_metric = getattr(Metrics(), main_metric_test.metric)
sorting = main_metric().sorting
sorted_result = sorted(
    results,
    key=lambda s: s.main_metric_result,
    reverse=(sorting != "descending"),
)

return sorted_result


async def leaderboard_handler(
        async_session: async_sessionmaker[AsyncSession],
        challenge_title: str,
) -> list[SubmissionInfo]:
    """
    Given challenge title returns the leaderboard fo rthe challenge, which is
    a list of submissions. For every user that takes part in the challenge only
    the best (given main metric) submission is taken into this list. The list
    is sorted by main metric.
    """
    # Checking challenge
    challenge_exists = await check_challenge_exists(
        async_session=async_session,
        title=challenge_title,
    )
    if not challenge_exists:
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title {
        challenge_title} does
        not exist
        ",
    )

    challenge = await get_challenge(
    async_session = async_session,
    title = challenge_title,

)

main_metric_test = await challenge_main_metric(
async_session = async_session,
challenge_id = challenge.id,
)

evaluations = await test_evaluations(
async_session = async_session,
test_id = main_metric_test.id,
)

submissions = await challenge_submissions(
async_session = async_session,
challenge_id = challenge.id,
)

submitters_ids = set([submission.submitter for submission in submissions])
submitters = []
for submitter_id in submitters_ids:
    submitters.append(
dict(
    id=submitter_id,
    name=await get_user_name(
        async_session=async_session,
        user_id=submitter_id,
    ),
)
)

main_metric = getattr(Metrics(), main_metric_test.metric)
sorting = main_metric().sorting

result = []
for submitter in submitters:
    submitter_submissions = [
submission.id
for submission in submissions
    if submission.submitter == submitter.get("id")
]

sorted_submitter_evaluations = sorted(
[
    evaluation
    for evaluation in evaluations
    if evaluation.submission in submitter_submissions
],
key = lambda x: x.score,
reverse = (sorting != "descending"),
)

if sorted_submitter_evaluations:
    best_result_evaluation = sorted_submitter_evaluations[0]
best_result_submission = next(
submission
for submission in submissions
    if submission.id == best_result_evaluation.submission
)

result.append(
SubmissionInfo(
    id=best_result_evaluation.submission,
    submitter=submitter.get("name"),
    description=best_result_submission.description,
    timestamp=best_result_submission.timestamp,
    main_metric_result=best_result_evaluation.score,
    additional_metrics_results=None,
)
)

for idx, submission_info in enumerate(result, start=1):
    submission_info.place = idx

result = sorted(
result, key = lambda d: d.main_metric_result, reverse = (sorting != "descending")
)

return result


async def delete_submission_handler(
        async_session: async_sessionmaker[AsyncSession],
        user_name: str,
        submission_id: int,
) -> None:
    user_exists = await check_user_exists(
        async_session=async_session,
        user_name=user_name,
    )
    if not user_exists:
        raise HTTPException(status_code=401, detail="User does not exist")

    submission_exists = await check_submission_exists(
        async_session=async_session,
        submission_id=submission_id,
    )
    if not submission_exists:
        raise HTTPException(status_code=422, detail="Submission does not exist")

    user = await get_user(
        async_session=async_session,
        user_name=user_name,
    )
    submission_belongs_to_user = await check_submission_author(
        async_session=async_session,
        submission_id=submission_id,
        user_id=user.id,
    )
    user_is_admin = await check_user_is_admin(
        async_session=async_session,
        user_name=user_name,
    )
    if (not submission_belongs_to_user) and (not user_is_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Submission does not belong to user or user is not an admin",
        )

    submission = await get_submission(
        async_session=async_session,
        submission_id=submission_id,
    )

    evaluations = await submission_evaluations(
        async_session=async_session,
        submission_id=submission_id,
    )

    await delete_evaluations(
        async_session=async_session,
        evaluations=evaluations,
    )

    await delete_submissions(
        async_session=async_session,
        submissions=[submission]
    )


async def edit_submission_handler(
        async_session: async_sessionmaker[AsyncSession],
        submission_id: int,
        user_name: str,
        description: str,
) -> None:
    """
    Allows to edit description of a submission.
    """
    submission_exists = await check_submission_exists(
        async_session=async_session,
        submission_id=submission_id,
    )
    if not submission_exists:
        raise HTTPException(
            status_code=422,
            detail=f"SUbmission does not exist",
        )

    user = await get_user(
        async_session=async_session,
        user_name=user_name,
    )
    submission_belongs_to_user = await check_submission_author(
        async_session=async_session,
        submission_id=submission_id,
        user_id=user.id,
    )
    user_is_admin = await check_user_is_admin(
        async_session=async_session,
        user_name=user_name,
    )
    if (not submission_belongs_to_user) and (not user_is_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Submission does not belong to user or user is not an admin",
        )

    await edit_submission(
        async_session=async_session,
        submission_id=submission_id,
        description=description,
    )

    return None
