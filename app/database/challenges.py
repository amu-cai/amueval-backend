from database.models import Challenge
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
)

"""
TODO move this to the endpoint
STORE_ENV = os.getenv("STORE_PATH")
if STORE_ENV is not None:
    STORE = STORE_ENV
else:
    raise FileNotFoundError("STORE_PATH env variable not defined")

challenges_dir = f"{STORE}/challenges"
"""


async def add_challenge(
    async_session: async_sessionmaker[AsyncSession],
    username: str,
    title: str,
    source: str,
    description: str,
    type: str,
    deadline: str,
    award: str,
    sorting: str,
):
    challenge = Challenge(
        author=username,
        title=title,
        type=type,
        source=source,
        description=description,
        deadline=deadline,
        award=award,
        sorting=sorting,
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
        session.add(challenge)

        await session.flush()

        challenge_id = challenge.id
        challenge_title = challenge.title

        await session.commit()

    return {
        "success": True,
        "challenge_title": challenge_title,
        "challenge_id": challenge_id,
        "message": "Challenge uploaded successfully",
    }
