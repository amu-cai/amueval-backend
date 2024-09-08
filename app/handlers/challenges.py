from fastapi import (
    HTTPException,
    UploadFile,
)
from pathlib import Path
from pydantic import (
    BaseModel,
    validator,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from database.challenges import (
    add_challenge,
    all_challenges,
    edit_challenge,
    check_challenge_author,
    check_challenge_exists,
)
from database.evaluations import (
    test_best_score,
)
from database.submissions import (
    challenge_participants,
)
from database.tests import (
    add_tests,
    challenge_main_metric,
)
from database.users import (
    check_user_exists,
    check_user_is_admin,
)
from handlers.files import save_expected_file
from metrics.metrics import Metrics


class CreateChallengeRerquest(BaseModel):
    author: str
    title: str
    source: str
    type: str
    description: str
    deadline: str
    award: str
    metric: str
    parameters: str
    sorting: str
    additional_metrics: str

    @validator("title")
    def title_does_not_contain_curses(cls, v):
        if "dupa" in v:
            raise ValueError("Name cannot contain curses")
        return v.title()


class CreateChallengeResponse(BaseModel):
    message: str = "Challenge created"
    challenge_title: str
    main_metric: str


class EditChallengeRerquest(BaseModel):
    user: str
    title: str
    description: str
    deadline: str


class GetChallengeResponse(BaseModel):
    id: int
    title: str
    type: str
    description: str
    main_metric: str
    best_sore: float
    deadline: str
    award: str
    deleted: bool
    sorting: str
    participants: int


class GetChallengesResponse(BaseModel):
    challenges: list[GetChallengeResponse]


async def create_challenge_handler(
    async_session: async_sessionmaker[AsyncSession],
    request: CreateChallengeRerquest,
    file: UploadFile,
) -> CreateChallengeResponse:
    """
    Creates a challenge from given @CreateChallengeRerquest and a '.tsv' file.
    Checks if:

    - user exists,
    - challenge of given title exists or the title is empty,
    - given file has '.tsv' extension.
    """
    # Checking user
    author_exists = await check_user_exists(
        async_session=async_session, user_name=request.author
    )
    if not author_exists:
        raise HTTPException(status_code=401, detail="User does not exist")

    # Checking title
    challenge_exists = await check_challenge_exists(
        async_session=async_session, title=request.title
    )
    if challenge_exists or request.title == "":
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title cannot be empty or challenge title <{
                request.title}> already exists",
        )

    # Checking file name
    proper_file_extension = ".tsv" == Path(file.filename).suffix
    if not proper_file_extension:
        raise HTTPException(
            status_code=415,
            detail=f"File <{file.filename}> is not a TSV file",
        )

    # Creating challenge
    added_challenge = await add_challenge(
        async_session=async_session,
        user_name=request.author,
        title=request.title,
        source=request.source,
        description=request.description,
        type=request.type,
        deadline=request.deadline,
        award=request.award,
    )

    # Creating tests for the challenge
    added_tests = await add_tests(
        async_session=async_session,
        challenge=added_challenge.get("challenge_id"),
        main_metric=request.metric,
        main_metric_parameters=request.parameters,
        additional_metrics=request.additional_metrics,
    )

    # Saving 'expected' file with name of the challenge
    await save_expected_file(file, request.title)

    return CreateChallengeResponse(
        challenge_title=added_challenge.get("challenge_title"),
        main_metric=added_tests.get("test_main_metric"),
    )


async def edit_challenge_handler(
    async_session: async_sessionmaker[AsyncSession],
    request: EditChallengeRerquest,
) -> None:
    if request.title == "":
        raise HTTPException(status_code=422, detail="Challenge title cannot be empty")

    challenge_exists = await check_challenge_exists(
        async_session=async_session, title=request.title
    )
    if not challenge_exists:
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title <{request.title}> does not exist",
        )

    challenge_belongs_to_user = await check_challenge_author(
        async_session=async_session,
        challenge_title=request.title,
        user_name=request.user,
    )
    user_is_admin = await check_user_is_admin(
        async_session=async_session,
        user_name=request.user,
    )
    if (not challenge_belongs_to_user) or (not user_is_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Challenge <{
                request.title}> does not belong to user <{request.user}> or user is not an admin",
        )

    await edit_challenge(
        async_session=async_session,
        title=request.title,
        description=request.description,
        deadline=request.deadline,
    )

    return None


async def get_challenges_handler(
    async_session: async_sessionmaker[AsyncSession],
) -> list[GetChallengeResponse]:
    challenges = await all_challenges(async_session=async_session)

    results = []
    for challenge in challenges:
        main_test = await challenge_main_metric(
            async_session=async_session,
            challenge_id=challenge.id,
        )

        main_metric = getattr(Metrics(), main_test.metric)
        sorting = main_metric().sorting

        participants = await challenge_participants(
            async_session=async_session, challenge_id=challenge.id
        )

        best_score = await test_best_score(
            async_session=async_session,
            test_id=main_test.id,
            sorting=sorting,
        )

        results.append(
            GetChallengeResponse(
                id=challenge.id,
                title=challenge.title,
                type=challenge.type,
                description=challenge.description,
                main_metric=main_test.metric,
                best_sore=best_score,
                deadline=challenge.deadline,
                award=challenge.award,
                deleted=challenge.deleted,
                sorting=sorting,
                participants=participants,
            )
        )

    return GetChallengesResponse(challenges=results)
