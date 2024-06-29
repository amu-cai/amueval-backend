from fastapi import UploadFile, File
from database.models import Challenge
from challenges.models import ChallengeInputModel
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)

import os

STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"


async def post_create_challenge(
    async_session: async_sessionmaker[AsyncSession],
    username: str,
    challenge_input_model: ChallengeInputModel,
    challenge_file: UploadFile = File(...),
):
    create_challenge_model = Challenge(
        author=username,
        title=challenge_input_model.title,
        type=challenge_input_model.type,
        source=challenge_input_model.challenge_source,
        description=challenge_input_model.description,
        main_metric=challenge_input_model.main_metric,
        main_metric_parameters=challenge_input_model.main_metric_parameters,
        best_score=None,
        deadline=challenge_input_model.deadline,
        award=challenge_input_model.award,
        sorting=challenge_input_model.sorting,
        readme="",
        deleted=False,
    )

    """
    TODO modify 'submit_test' for new files layout
    try:
        await submit_test(
            username=username,
            description=challenge_input_model.description,
            challenge=create_challenge_model,
            sub_file_path=temp_zip_path,
        )
    except Exception as err:
        shutil.rmtree(f"{challenges_dir}/{challenge_folder_name}")
        raise HTTPException(status_code=422, detail=f"Test submission error {err}")
    """

    async with async_session as session:
        session.add(create_challenge_model)
        await session.commit()

    return {
        "success": True,
        "challenge": challenge_input_model.title,
        "message": "Challenge uploaded successfully",
    }
