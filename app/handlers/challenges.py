from fastapi import (
    HTTPException,
    UploadFile,
    status,
)
from pathlib import Path
from pydantic import (
    BaseModel,
    validator,
)
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)

from database.challenges import (
    add_challenge,
    check_challenge_exists,
)
from database.tests import add_tests
from database.users import check_user_exists
from handlers.files import save_expected_file


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


async def create_challenge_handler(
    async_session: async_sessionmaker[AsyncSession],
    request: CreateChallengeRerquest,
    file: UploadFile,
) -> CreateChallengeResponse:
    """
    Description
    """
    # Checking user
    author_exists = await check_user_exists(
        async_session=async_session, user_name=request.author
    )
    if not author_exists:
        raise HTTPException(status_code=401, detail="User does not exist")

    # Checking title
    if request.title == "":
        raise HTTPException(status_code=422, detail="Challenge title cannot be empty")

    challenge_exists = await check_challenge_exists(
        async_session=async_session, title=request.title
    )
    if challenge_exists:
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title <{request.title}> already exists",
        )

    # Checking file name
    proper_file_extension = ".tsv" == Path(file.filename).suffix
    if not proper_file_extension:
        raise HTTPException(
            status_code=422,
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

    response = CreateChallengeResponse(
        challenge_title=added_challenge.get("challenge_title"),
        main_metric=added_tests.get("test_main_metric"),
    )
    return response
