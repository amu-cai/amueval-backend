from typing import Annotated
from fastapi import Depends, FastAPI, status, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import UploadFile, File
from challenges.models import ChallengeInputModel
from auth.models import CreateUserRequest, Token
import auth.auth as auth
import challenges.challenges as challenges
import evaluation.evaluation as evaluation
from database_handler.db_connection import get_engine, get_session
from database_handler.base_table import Base
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = get_engine()
session = get_session(engine)

# postgre async db
async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db = session()
    try:
        yield db
    finally:
        await db.close()

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth.get_current_user)]

auth_router = APIRouter(
    prefix="/auth",
    tags=['auth']
)

@auth_router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    return await auth.create_user(async_session=db, create_user_request=create_user_request)

@auth_router.post("/login", response_model=Token)
async def login_for_access_token(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return await auth.login_for_access_token(async_session=db, form_data=form_data)

challenges_router = APIRouter(
    prefix="/challenges",
    tags=['challenges']
)

@challenges_router.post("/create-challenge")
async def create_challenge(db: db_dependency,  user: user_dependency,
                            challenge_title: Annotated[str, Form()], 
                            challenge_source: Annotated[str, Form()] = "", 
                            description: Annotated[str, Form()] = "", 
                            deadline: Annotated[str, Form()] = "",
                            award: Annotated[str, Form()] = "", 
                            type: Annotated[str, Form()] = "",
                            metric: Annotated[str, Form()] = "",
                            challenge_file:UploadFile = File(...)):
    await auth.check_user_exists(async_session=db, username=user["username"])
    challenge_input_model: ChallengeInputModel = ChallengeInputModel(
        title = challenge_title,
        challenge_source = challenge_source,
        description = description,
        type = type,
        main_metric = metric,
        deadline = deadline,
        award = award,
    )
    return await challenges.create_challenge(async_session=db, user=user, challenge_file=challenge_file, challenge_input_model=challenge_input_model)

@challenges_router.get("/get-challenges")
async def get_challenges(db: db_dependency):
    return await challenges.all_challenges(async_session=db)

@challenges_router.get("/challenge/{challenge}")
async def get_challenge_readme(db: db_dependency, challenge: str):
    return await challenges.get_challenge_info(async_session=db, challenge=challenge)

evaluation_router = APIRouter(
    prefix="/evaluation",
    tags=['evaluation']
)

@evaluation_router.post("/submit")
async def submit(db: db_dependency, user: user_dependency, description: Annotated[str, Form()], challenge_title: Annotated[str, Form()], submission_file: UploadFile = File(...)):
    await auth.check_user_exists(async_session=db, username=user["username"])
    return await evaluation.submit(async_session=db, user=user, submission_file=submission_file, challenge_title=challenge_title, description=description)

@evaluation_router.get("/get-metrics")
async def get_metrics():
    return await evaluation.get_metrics()

@evaluation_router.get("/{challenge}/all-submissions/")
async def get_all_submissions(db: db_dependency, challenge: str):
    return await evaluation.get_all_submissions(async_session=db, challenge=challenge)

@evaluation_router.get("/{challenge}/my-submissions/")
async def get_my_submissions(db: db_dependency, challenge: str, user: user_dependency):
    await auth.check_user_exists(async_session=db, username=user["username"])
    return await evaluation.get_my_submissions(async_session=db, challenge=challenge, user=user)

@evaluation_router.get("/{challenge}/leaderboard/")
async def get_leaderboard(db: db_dependency, challenge: str):
    return await evaluation.get_leaderboard(async_session=db, challenge=challenge)

app.include_router(auth_router)
app.include_router(challenges_router)
app.include_router(evaluation_router)

@app.get("/auth", status_code=status.HTTP_200_OK)
async def user(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return {"User": user}

