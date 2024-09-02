from fastapi import UploadFile
from os import getenv
from pathlib import Path


STORE_ENV = getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")


challenges_dir = f"{STORE}/challenges"


async def save_expected_file(file: UploadFile, file_name: str) -> Path:
    file_full_name = f"{file_name}.tsv"
    file_path = Path(challenges_dir, file_full_name)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return file_path
