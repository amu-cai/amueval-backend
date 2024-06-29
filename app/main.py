from pathlib import Path
from typing import Annotated
from fastapi import Depends, FastAPI, status, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import UploadFile, File
from challenges.models import ChallengeInputModel
from admin.models import UserRightsModel
from auth.models import CreateUserRequest, Token, EditUserRequest
import auth.auth as auth
import challenges.challenges as challenges
import evaluation.evaluation as evaluation
import admin.admin as admin
from database.db_connection import get_engine, get_session
from database.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from global_helper import (
    check_challenge_exists,
    save_expected_file,
)
from database.challenges import add_challenge

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


challenges_router = APIRouter(prefix="/challenges", tags=["challenges"])


@challenges_router.post("/create-challenge1")
async def create_challenge1(
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
    sorting: Annotated[str, Form()] = "",
    challenge_file: UploadFile = File(...),
    additional_metrics: Annotated[str, Form()] = "",
):
    # TODO move db methods to their src files and thor exceptions only from
    # endpoints
    await auth.check_user_exists(async_session=db, username=user["username"])

    if challenge_title == "":
        raise HTTPException(status_code=422, detail="Challenge title cannot be empty")

    challenge_exists = await check_challenge_exists(db, challenge_title)
    if challenge_exists:
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title <{challenge_title}> already exists",
        )

    proper_file_extension = ".tsv" == Path(challenge_file.filename).suffix
    if not proper_file_extension:
        raise HTTPException(
            status_code=422,
            detail=f"File <{challenge_file.filename}> is not a TSV file",
        )

    await save_expected_file(challenge_file, challenge_title)

    added_challenge = await add_challenge(
        async_session=db,
        username=user["username"],
        title=challenge_title,
        type=type,
        source=challenge_source,
        description=description,
        best_score=None,
        deadline=deadline,
        award=award,
        sorting=sorting,
        readme="",
        deleted=False,
    )

    create_metrics = await create_tests(
        main_metric=metric,
        main_metric_parameters=parameters,
        additional_metrics=additional_metrics,
    )

    return {
        "success": True,
        "message": "Challenge uploaded successfully",
        "challenge_title": added_challenge.title,
    }


@challenges_router.post("/create-challenge")
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
    sorting: Annotated[str, Form()] = "",
    challenge_file: UploadFile = File(...),
):
    await auth.check_user_exists(async_session=db, username=user["username"])
    challenge_input_model: ChallengeInputModel = ChallengeInputModel(
        title=challenge_title,
        challenge_source=challenge_source,
        description=description,
        type=type,
        main_metric=metric,
        main_metric_parameters=parameters,
        deadline=deadline,
        award=award,
        sorting=sorting,
    )
    return await challenges.create_challenge(
        async_session=db,
        username=user["username"],
        challenge_file=challenge_file,
        challenge_input_model=challenge_input_model,
    )


@challenges_router.get("/get-challenges")
async def get_challenges(db: db_dependency):
    return await challenges.all_challenges(async_session=db)


@challenges_router.get("/challenge/{challenge}")
async def get_challenge_info(db: db_dependency, challenge: str):
    return await challenges.get_challenge_info(async_session=db, challenge=challenge)


evaluation_router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@evaluation_router.post("/submit")
async def submit(
    db: db_dependency,
    user: user_dependency,
    description: Annotated[str, Form()],
    challenge_title: Annotated[str, Form()],
    submission_file: UploadFile = File(...),
):
    await auth.check_user_exists(async_session=db, username=user["username"])
    challenge_exists = await check_challenge_exists(
        async_session=db, title=challenge_title
    )
    if not challenge_exists:
        raise HTTPException(
            status_code=422, detail=f"{challenge_title} challenge not exist!"
        )
    return await evaluation.submit(
        async_session=db,
        username=user["username"],
        submission_file=submission_file,
        challenge_title=challenge_title,
        description=description,
    )


@evaluation_router.get("/get-metrics")
async def get_metrics():
    return await evaluation.get_metrics()


@evaluation_router.get("/{challenge}/all-submissions")
async def get_all_submissions(db: db_dependency, challenge: str):
    return await evaluation.get_all_submissions(async_session=db, challenge=challenge)


@evaluation_router.get("/{challenge}/my-submissions")
async def get_my_submissions(db: db_dependency, challenge: str, user: user_dependency):
    await auth.check_user_exists(async_session=db, username=user["username"])
    return await evaluation.get_my_submissions(
        async_session=db, challenge=challenge, user=user
    )


@evaluation_router.get("/{challenge}/leaderboard")
async def get_leaderboard(db: db_dependency, challenge: str):
    return await evaluation.get_leaderboard(async_session=db, challenge=challenge)


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
    await auth.check_user_exists(async_session=db, username=user["username"])
    await auth.check_user_is_admin(async_session=db, username=user["username"])
    await check_challenge_exists(async_session=db, title=challenge_title)
    return await admin.delete_challenge(
        async_session=db, challenge_title=challenge_title
    )


app.include_router(auth_router)
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
