import auth.auth as auth
import evaluation.evaluation as evaluation
import admin.admin as admin

from fastapi import Depends, FastAPI, status, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import UploadFile, File
from pydantic import ValidationError, BaseModel
from typing import Annotated

from admin.models import UserRightsModel
from auth.models import CreateUserRequest, Token, EditUserRequest
from database.db_connection import get_engine, get_session
from database.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from database.challenges import (
    check_challenge_exists,
)
from database.users import get_user_submissions, get_user_challenges

from handlers.challenges import (
    ChallengeInfoResponse,
    CreateChallengeRerquest,
    CreateChallengeResponse,
    EditChallengeRerquest,
    challenge_info_handler,
    create_challenge_handler,
    edit_challenge_handler,
    get_challenges_handler,
)
from handlers.evaluations import (
    CreateSubmissionRequest,
    challenge_submissions_handler,
    create_submission_handler,
    get_metrics_handler,
)


engine = get_engine()
session = get_session(engine)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# postgre async db
async def get_db():
    db = session()
    try:
        yield db
    finally:
        await db.close()


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_dependency = Annotated[dict, Depends(auth.get_current_user)]
db_dependency = Annotated[AsyncSession, Depends(get_db)]


class ErrorMessage(BaseModel):
    message: str


@app.on_event("startup")
async def startup():
    await create_tables()


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    return await auth.create_user(
        async_session=db, create_user_request=create_user_request
    )


@auth_router.post("/login", response_model=Token)
async def login_for_access_token(
    db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    return await auth.login_for_access_token(async_session=db, form_data=form_data)


@auth_router.get("/user-rights-info")
async def get_user_rights_info(db: db_dependency, user: user_dependency):
    await auth.check_user_exists(async_session=db, username=user["username"])
    return await auth.get_user_rights_info(async_session=db, username=user["username"])


@auth_router.get("/profile-info")
async def get_profile_info(db: db_dependency, user: user_dependency):
    await auth.check_user_exists(async_session=db, username=user["username"])
    return await auth.get_profile_info(async_session=db, username=user["username"])


@auth_router.put("/profile/edit")
async def edit_user(
    db: db_dependency, user: user_dependency, edit_user_request: EditUserRequest
):
    await auth.check_user_exists(async_session=db, username=user["username"])
    return await auth.edit_user(
        async_session=db, username=user["username"], edit_user_request=edit_user_request
    )


user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post("/submissions")
async def user_submissions(
    db: db_dependency,
    user: user_dependency,
):
    return await get_user_submissions(async_session=db, user_name=user["username"])


@user_router.post("/challenges")
async def user_challenges(
    db: db_dependency,
    user: user_dependency,
):
    return await get_user_challenges(async_session=db, user_name=user["username"])


challenges_router = APIRouter(prefix="/challenges", tags=["challenges"])


@challenges_router.post(
    "/create-challenge",
    response_model=CreateChallengeResponse,
    summary="Creates a challenge",
    description="Creates a challenge given required data and a '.tsv' file.",
    status_code=201,
    responses={
        400: {"model": ErrorMessage, "description": "Input data validation error"},
        401: {"model": ErrorMessage, "description": "User does not exist"},
        415: {
            "model": ErrorMessage,
            "description": "File <filename> is not a TSV file",
        },
        422: {
            "model": ErrorMessage,
            "description": "Challenge title cannot be empty or challenge title <challenge title> already exists",
        },
    },
)
async def create_challenge(
    db: db_dependency,
    user: user_dependency,
    challenge_title: Annotated[str, Form()],
    challenge_source: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    deadline: Annotated[str, Form()] = "",
    award: Annotated[str, Form()] = "",
    type: Annotated[str, Form()] = "",
    metric: Annotated[str, Form()] = "",
    parameters: Annotated[str, Form()] = "",
    # TODO: Check if 'sorting' is still needed
    sorting: Annotated[str, Form()] = "",
    challenge_file: UploadFile = File(...),
    additional_metrics: Annotated[str, Form()] = "",
):
    """
    Creates challenge from given data. In order to check, if the data is in the
    right format, it will try to convert input data to @CreateChallengeRerquest
    model. The rest of the checks is performed in @create_challenge_handler.
    """

    try:
        request = CreateChallengeRerquest(
            author=user["username"],
            title=challenge_title,
            source=challenge_source,
            type=type,
            description=description,
            deadline=deadline,
            award=award,
            metric=metric,
            parameters=parameters,
            sorting=sorting,
            additional_metrics=additional_metrics,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=e.json(),
        )

    return await create_challenge_handler(
        async_session=db,
        request=request,
        file=challenge_file,
    )


@challenges_router.put(
    "/edit-challenge",
    summary="Edits a challenge",
    description="Changes description and deadline for a given challenge. Olny\
        user that created the challenge and admin are authorized to do this.",
    status_code=200,
    responses={
        400: {"model": ErrorMessage, "description": "Input data validation error"},
        403: {
            "model": ErrorMessage,
            "description": "Challenge <challenge title> does not belong to user <user_name> or user is not an admin",
        },
        422: {
            "model": ErrorMessage,
            "description": "Challenge title <challenge title> does not exist",
        },
    },
)
async def edit_challenge(
    db: db_dependency,
    user: user_dependency,
    challenge_title: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    deadline: Annotated[str, Form()] = "",
):
    """
    Changes description and deadline for a given challenge.
    """

    try:
        request = EditChallengeRerquest(
            user=user.get("username"),
            title=challenge_title,
            description=description,
            deadline=deadline,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=e.json(),
        )

    return await edit_challenge_handler(
        async_session=db,
        request=request,
    )


@challenges_router.get(
    "/get-challenges",
    summary="Gives list of all challenges",
    description="Returns a list of all active challenges.",
    status_code=200,
)
async def get_challenges(db: db_dependency):
    challenges = (await get_challenges_handler(async_session=db)).challenges

    # TODO: change the input for the nedpoint for the model and the output, also
    # to the model
    challenges_dicts = [c.model_dump() for c in challenges]

    return challenges_dicts


@challenges_router.get(
    "/challenge/{challenge}",
    summary="Information about a challenge",
    description="Returns information for a given challenge.",
    response_model=ChallengeInfoResponse,
    status_code=200,
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Challenge <challenge title> does not exist",
        },
    },
)
async def get_challenge_info(db: db_dependency, challenge: str):
    response = await challenge_info_handler(async_session=db, title=challenge)
    return response.model_dump()


evaluation_router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@evaluation_router.post(
    "/submit",
    summary="Submitt a solution",
    description="Submitt a solution with a description.",
    status_code=200,
    responses={
        400: {"model": ErrorMessage, "description": "Input data validation error"},
        401: {"model": ErrorMessage, "description": "User does not exist"},
        403: {
            "model": ErrorMessage,
            "description": "Submission after deadline",
        },
        415: {
            "model": ErrorMessage,
            "description": "File <filename> is not a TSV file",
        },
    },
)
async def submit(
    db: db_dependency,
    user: user_dependency,
    description: Annotated[str, Form()],
    challenge_title: Annotated[str, Form()],
    submission_file: UploadFile = File(...),
):
    try:
        request = CreateSubmissionRequest(
            author=user.get("username"),
            challenge_title=challenge_title,
            description=description,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=e.json(),
        )

    return await create_submission_handler(
        async_session=db,
        request=request,
        file=submission_file,
    )


@evaluation_router.get(
    "/get-metrics",
    summary="List of all available metrics",
    description="List of all available metrics",
    status_code=200,
)
async def get_metrics():
    return await get_metrics_handler()


@evaluation_router.get(
    "/{challenge}/all-submissions",
    summary="List of submissions for a challenge",
    description="List of all submissions for a given challenge. If user\
        submitted many submissions, then this list will contain all of them.",
    status_code=200,
    responses={
        422: {
            "model": ErrorMessage,
            "description": "Challenge title <challenge title> does not exist",
        },
    },
)
async def get_challenge_all_submissions(
    db: db_dependency,
    challenge: str,
):
    submissions = await challenge_submissions_handler(
        async_session=db,
        challenge_title=challenge,
    )
    response = [s.model_dump() for s in submissions]
    return response


@evaluation_router.get(
    "/{challenge}/my-submissions",
    summary="List of submissions created by a given user",
    description="List of submissions created by a given user",
    status_code=200,
    responses={
        401: {"model": ErrorMessage, "description": "User does not exist"},
        422: {
            "model": ErrorMessage,
            "description": "Challenge title <challenge title> does not exist",
        },
    },
)
async def get_user_submissions_for_challenge(
    db: db_dependency,
    challenge: str,
    user: user_dependency,
):
    submissions = await challenge_submissions_handler(
        async_session=db,
        challenge_title=challenge,
        user=user,
    )
    response = [s.model_dump() for s in submissions]
    return response


@evaluation_router.get("/{challenge}/leaderboard")
async def get_leaderboard(db: db_dependency, challenge: str):
    return await evaluation.get_leaderboard(async_session=db, challenge_name=challenge)


admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/users-settings")
async def get_user_settings(db: db_dependency, user: user_dependency):
    await auth.check_user_exists(async_session=db, username=user["username"])
    await auth.check_user_is_admin(async_session=db, username=user["username"])
    return await admin.get_users_settings(async_session=db)


@admin_router.post("/user-rights-update")
async def user_rights_update(
    db: db_dependency, user: user_dependency, user_rights: UserRightsModel
):
    await auth.check_user_exists(async_session=db, username=user["username"])
    await auth.check_user_exists(async_session=db, username=user_rights.username)
    await auth.check_user_is_admin(async_session=db, username=user["username"])
    if not user_rights.is_admin and user_rights.username == user["username"]:
        raise HTTPException(
            status_code=401,
            detail="Remove admin failed! Can not remove admin from self.",
        )
    return await admin.user_rights_update(async_session=db, user_rights=user_rights)


@admin_router.post("/delete-challenge/{challenge_title}")
async def delete_challenge(
    db: db_dependency, user: user_dependency, challenge_title: str
):
    await auth.check_user_is_admin(async_session=db, username=user["username"])

    challenge_exists = await check_challenge_exists(db, challenge_title)
    if not challenge_exists:
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title <{challenge_title}> does not exist",
        )

    return await admin.delete_challenge(
        async_session=db, challenge_title=challenge_title
    )


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(challenges_router)
app.include_router(evaluation_router)
app.include_router(admin_router)


@app.get("/auth", status_code=status.HTTP_200_OK)
async def user(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return {"User": user}


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "Info": "api launched successfully, go to docs/ to see available endpoints."
    }
