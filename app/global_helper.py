from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import (
    select,
)
from database.models import Challenge
from secrets import token_hex
import os
from fastapi import HTTPException, UploadFile

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")


challenges_dir = f"{STORE}/challenges"


async def check_challenge_exists(
    async_session: async_sessionmaker[AsyncSession],
    title: str,
) -> bool:
    async with async_session as session:
        challenge_exists = (
            await session.execute(select(Challenge.title).filter_by(title=title))
        ).fetchone() is not None
        await session.commit()

    return challenge_exists


async def save_expected_file(file: UploadFile, file_name: str) -> str:
    file_full_name = f"{file_name}.tsv"
    file_path = f"{challenges_dir}/{file_full_name}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    """
    TODO write as the following
    try:
        with open(file.filename, 'wb') as f:
            shutil.copyfileobj(file.file, f)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()
    """
    return file_path


def check_file_extension(file, extension="zip"):
    file_ext = file.filename.split(".").pop()
    if file_ext != extension:
        raise HTTPException(status_code=422, detail="Bad extension")
