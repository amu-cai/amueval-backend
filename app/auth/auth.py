import base64
import datetime
import json

from datetime import timedelta
from typing import Annotated
from fastapi import Depends, HTTPException
from starlette import status
from database.models import User, Challenge, Submission
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from auth.models import CreateUserRequest, EditUserRequest
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import (
    select,
)
from auth.auth_helper import valid_email, valid_password, valid_username
import os

KEY_ENV = os.getenv("KEY")
if KEY_ENV is not None:
    SECRET_KEY = KEY_ENV
else:
    raise FileNotFoundError("KEY env variable not defined")

ALG_ENV = os.getenv("ALGORITHM")
if ALG_ENV is not None:
    ALGORITHM = ALG_ENV
else:
    raise FileNotFoundError("ALGORITHM env variable not defined")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


async def authenticate_user(
    username: str, password: str, async_session: async_sessionmaker[AsyncSession]
):
    async with async_session as session:
        try:
            user = (
                (await session.execute(select(User).filter_by(username=username)))
                .scalars()
                .one()
            )
        except:
            user = False
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def check_user_exists(
    async_session: async_sessionmaker[AsyncSession], username: str
):
    async with async_session as session:
        user_exist = len(
            (await session.execute(select(User).filter_by(username=username)))
            .scalars()
            .all()
        )
    if user_exist:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password.",
        )


async def check_user_is_admin(
    async_session: async_sessionmaker[AsyncSession], username: str
):
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=username)))
            .scalars()
            .one()
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied, administrator rights needed",
        )


async def check_user_is_admin1(
    async_session: async_sessionmaker[AsyncSession], user_name: str
):
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=user_name)))
            .scalars()
            .one()
        )

        user_is_admin = user.is_admin

    return user_is_admin


async def get_current_user_data(token: Annotated[str, Depends(oauth2_bearer)]) -> dict[str, str]:
    try:
        split_token = token.split(".")
        # token_header = split_token[0]
        # decoded_header = base64.urlsafe_b64decode(token_header + '=' * (-len(token_header) % 4)).decode("utf-8")

        body = split_token[1]
        decoded_body = base64.urlsafe_b64decode(body + '=' * (-len(token) % 4)).decode("utf-8")
        body_json = json.loads(decoded_body)

        exp_time = body_json.get("exp")
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp()
        if exp_time < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )

        email = body_json.get("email")
        username = body_json.get("preferred_username")

        return {"username": username, "email": email}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password.",
        )


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login or password.",
            )
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password.",
        )


async def create_user(
    async_session: async_sessionmaker[AsyncSession],
    create_user_request: CreateUserRequest,
):
    async with async_session as session:
        users = (await session.execute(select(User))).scalars().all()
        users_exist = len(users) > 0
        username = (
            (
                await session.execute(
                    select(User).filter_by(username=create_user_request.username)
                )
            )
            .scalars()
            .all()
        )
        username_already_exist = len(username) > 0
        email = (
            (
                await session.execute(
                    select(User).filter_by(email=create_user_request.email)
                )
            )
            .scalars()
            .all()
        )
        email_already_exist = len(email) > 0

    if username_already_exist:
        raise HTTPException(
            status_code=422,
            detail=f"Username {create_user_request.username} already exist!",
        )

    if email_already_exist:
        raise HTTPException(
            status_code=422,
            detail=f"Account with email {
                create_user_request.email} already exist!",
        )

    if not valid_username(create_user_request.username):
        raise HTTPException(status_code=422, detail=f"Username is required!")

    if not valid_password(create_user_request.password):
        raise HTTPException(
            status_code=422, detail=f"Password must have at least 10 characters"
        )

    if not valid_email(create_user_request.email):
        raise HTTPException(status_code=422, detail=f"Invalid email format")

    is_admin = False
    if not users_exist:
        is_admin = True

    create_user_model = User(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_admin=is_admin,
        is_author=True,
    )

    async with async_session as session:
        async_session.add(create_user_model)
        await session.commit()

    return {"message": f"user {create_user_request.username} created!"}


async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    async_session: async_sessionmaker[AsyncSession],
):
    user = await authenticate_user(
        form_data.username, form_data.password, async_session
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password.",
        )
    token = create_access_token(user.username, user.id, timedelta(minutes=1440))

    return {"access_token": token, "token_type": "bearer"}


async def get_user_rights_info(
    async_session: async_sessionmaker[AsyncSession], username: str
):
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=username)))
            .scalars()
            .one()
        )
    return {"isAdmin": user.is_admin, "isAuthor": user.is_author}


async def get_profile_info(
    async_session: async_sessionmaker[AsyncSession], username: str
):
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=username)))
            .scalars()
            .one()
        )

        challenges_number = len(
            (await session.execute(select(Challenge).filter_by(author=username)))
            .scalars()
            .all()
        )

        submissions_number = len(
            (await session.execute(select(Submission).filter_by(submitter=user.id)))
            .scalars()
            .all()
        )

    return dict(
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        is_author=user.is_author,
        challenges_number=challenges_number,
        submissions_number=submissions_number,
    )


async def edit_user(
    async_session: async_sessionmaker[AsyncSession],
    username: str,
    edit_user_request: EditUserRequest,
):
    async with async_session as session:
        user = (
            (await session.execute(select(User).filter_by(username=username)))
            .scalars()
            .one()
        )
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with username {username} not found!"
            )

        user.email = edit_user_request.email

        await session.commit()

    return {"message": f"User with username {username} updated!"}
