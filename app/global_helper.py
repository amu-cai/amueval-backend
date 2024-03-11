from glob import glob
import json
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

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"

def check_challenge_in_store(challenge_folder_name):
    current_challenges = [x.replace(f"{challenges_dir}/", '') for x in glob(f"{challenges_dir}/*")]
    if challenge_folder_name in current_challenges:
        return True

def check_zip_structure(zip_ref, folder_name, required_files):
    challenge_files = [file_obj.filename for file_obj in zip_ref.filelist]
    for file in required_files:
        if not f"{folder_name}/{file}" in challenge_files:
            return True

async def check_challenge_exists(
    async_session: async_sessionmaker[AsyncSession],
    title: str,
) -> bool:
    async with async_session as session:
        challenge_exists = (
            await session.execute(
                select(Challenge.title).filter_by(title=title)
            )
        ).fetchone() is not None
    return challenge_exists

async def save_zip_file(file):
    file_name = token_hex(10)
    file_path = f"{file_name}.zip"
    temp_zip_path = f"{STORE}/temp/{file_path}"
    with open(temp_zip_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return temp_zip_path