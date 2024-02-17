from database_sqlite.models import Submission
import evaluation.evaluation_helper as evaluation_helper
from datetime import datetime
from fastapi import UploadFile, File, Form, HTTPException
import zipfile
from global_helper import check_challenge_in_store, check_zip_structure, save_zip_file, check_challenge_exists
import os
import json
from sqlalchemy import (
    select,
)

f = open('configure.json')
data = json.load(f)
STORE = data['store_path']
challenges_dir = f"{STORE}/challenges"

async def submit(async_session, description, challenge_title, submitter, submission_file:UploadFile = File(...)):
    challenge_exists = await check_challenge_exists(async_session, challenge_title)
    if not challenge_exists:
        raise HTTPException(status_code=422, detail=f'{challenge_title} challenge not exist!')

    submitter = evaluation_helper.check_submitter(submitter)
    description = evaluation_helper.check_description(description)

    temp_zip_path = await save_zip_file(submission_file)

    dev_result = 0
    test_result = 0

    required_submission_files = ["dev-0/out.tsv", "test-A/out.tsv"]
    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
        challenge_name = zip_ref.filelist[0].filename[:-1]

        folder_name_error = not challenge_title == challenge_name
        challenge_not_exist_error = not check_challenge_in_store(challenge_name)
        structure_error = check_zip_structure(zip_ref, challenge_name, required_submission_files)

        if True not in [folder_name_error, challenge_not_exist_error, structure_error]:
            for file in zip_ref.filelist:
                if file.filename == f"{challenge_name}/dev-0/out.tsv":
                    with zip_ref.open(file, "r") as file_content:
                        dev_from_challenge = open(f"{challenges_dir}/{challenge_name}/dev-0/expected.tsv", "r")
                        from_challenge_num = int(dev_from_challenge.readlines()[0])

                        print("from_challenge_num")
                        print(from_challenge_num)

                        from_submission_num = int(file_content.readlines()[0])

                        print("from_submission_num")
                        print(from_submission_num)

                        dev_result = from_challenge_num + from_submission_num

                if file.filename == f"{challenge_name}/test-A/out.tsv":
                    with zip_ref.open(file, "r") as file_content:
                        test_from_challenge = open(f"{challenges_dir}/{challenge_name}/test-A/expected.tsv", "r")
                        from_challenge_num = int(test_from_challenge.readlines()[0])

                        print("from_challenge_num")
                        print(from_challenge_num)

                        from_submission_num = int(file_content.readlines()[0])

                        print("from_submission_num")
                        print(from_submission_num)

                        test_result = from_challenge_num + from_submission_num

    os.remove(temp_zip_path)

    if folder_name_error:
        raise HTTPException(status_code=422, detail=f'Invalid challenge folder name "{challenge_name}" - is not equal to challenge title "{challenge_title}"')

    if challenge_not_exist_error:
        raise HTTPException(status_code=422, detail=f'Challenge "{challenge_name}" not exist in store!')

    if structure_error:
        raise HTTPException(status_code=422, detail=f'Bad challenge structure! Challenge required files: {str(required_submission_files)}')

    timestamp = datetime.now().strftime("%d-%m-%Y, %H:%M:%S")

    create_submission_model = Submission(
        challenge = challenge_title,
        submitter = submitter,
        description = description,
        dev_result = str(dev_result),
        test_result = str(test_result),
        timestamp = timestamp,
    )

    async with async_session as session:
        session.add(create_submission_model)
        await session.commit()

    return {"success": True, "submission": "description", "message": "Submission added successfully"}

async def get_metrics():
    result =  [{"name": "Accuracy"}, {"name": "Precision"}]
    return result

async def get_all_submissions(async_session, challenge: str):
    result = []

    async with async_session as session:
        submissions = await session.execute(select(Submission))

    for submission in submissions.scalars().all():
        result.append({
            "id": submission.id,
            "submitter": submission.submitter,
            "description": submission.description,
            "dev_result": submission.dev_result,
            "test_result": submission.test_result,
            "timestamp": submission.timestamp,
        })
    return result