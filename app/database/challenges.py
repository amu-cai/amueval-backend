from sqlalchemy import (
    exists,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from database.models import Challenge


async def add_challenge(
    async_session: async_sessionmaker[AsyncSession],
    user_name: str,
    title: str,
    source: str,
    description: str,
    type: str,
    deadline: str,
    award: str,
):
    challenge = Challenge(
        author=user_name,
        title=title,
        type=type,
        source=source,
        description=description,
        deadline=deadline,
        award=award,
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
        "challenge_title": challenge_title,
        "challenge_id": challenge_id,
    }


async def check_challenge_exists(
    async_session: async_sessionmaker[AsyncSession], title: str
) -> bool:
    async with async_session as session:
        challenge_exist = (
            await session.execute(
                exists(Challenge).where(Challenge.title == title).select()
            )
        ).scalar()

    return challenge_exist
