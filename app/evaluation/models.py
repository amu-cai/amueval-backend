from pydantic import BaseModel


class SubmitInputModel(BaseModel):
    challenge_title: str
    submitter: str
    description: str
    repo_url: str
