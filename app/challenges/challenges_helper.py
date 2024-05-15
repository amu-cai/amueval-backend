import zipfile
import os
from global_helper import check_challenge_in_store, check_zip_structure
from fastapi import HTTPException
from shutil import rmtree
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)
from os.path import exists
from sqlalchemy import (
    select,
)

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"


def check_challenge_title(challenge_title):
    if challenge_title == "":
        raise HTTPException(
            status_code=422, detail=f"{challenge_title}: Invalid challenge title"
        )


async def extract_challenge(challenge_title, temp_zip_path, challenges_dir):
    required_challenge_files = [
        "README.md",
        "dev-0/expected.tsv",
        "test-A/expected.tsv",
    ]

    with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
        challenge_name = zip_ref.filelist[0].filename[:-1]

        folder_name_error = not challenge_title == challenge_name
        challenge_already_exist_error = check_challenge_in_store(challenge_name)
        structure_error = check_zip_structure(
            zip_ref, challenge_name, required_challenge_files
        )

        if True not in [  # if not any(...)
            folder_name_error,
            challenge_already_exist_error,
            structure_error,
        ]:
            for file in required_challenge_files:
                zip_ref.extract(f"{challenge_name}/{file}", challenges_dir)

    if folder_name_error:
        os.remove(temp_zip_path)
        if exists(f"{challenges_dir}/{challenge_name}"):
            rmtree(f"{challenges_dir}/{challenge_name}")
        raise HTTPException(
            status_code=422,
            detail=f'Invalid challenge folder name "{challenge_name}" - is not equal to challenge title "{challenge_title}"',
        )

    if challenge_already_exist_error:
        os.remove(temp_zip_path)
        if exists(f"{challenges_dir}/{challenge_name}"):
            rmtree(f"{challenges_dir}/{challenge_name}")
        raise HTTPException(
            status_code=422,
            detail=f'Challenge "{challenge_name}" already exist in store!',
        )

    if structure_error:
        os.remove(temp_zip_path)
        if exists(f"{challenges_dir}/{challenge_name}"):
            rmtree(f"{challenges_dir}/{challenge_name}")
        raise HTTPException(
            status_code=422,
            detail=f"Bad challenge structure! Challenge required files: {str(required_challenge_files)}",
        )

    return challenge_name
