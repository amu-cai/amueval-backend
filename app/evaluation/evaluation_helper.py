import zipfile
import os
from fastapi import HTTPException
from secrets import token_hex

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"


async def save_zip_file(file):
    file_name = token_hex(10)
    file_path = f"{file_name}.zip"
    temp_zip_path = f"{STORE}/temp/{file_path}"
    with open(temp_zip_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return temp_zip_path


async def extract_submission(temp_zip_path):
    required_files = ["dev-0/out.tsv", "test-A/out.tsv"]
    with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
        challenge_name = zip_ref.filelist[0].filename[:-1]
        submission_dir = f"{challenges_dir}/{challenge_name}/submissions"
        for file in required_files:
            zip_ref.extract(f"{challenge_name}/{file}", submission_dir)
    os.remove(temp_zip_path)


def check_repo_url(repo_url):
    if repo_url == "":
        raise HTTPException(status_code=422, detail="Bad repo url")


def check_submitter(submitter):
    if submitter == "x":
        submitter = "anonymous"
    return submitter


def check_description(description):
    return description
