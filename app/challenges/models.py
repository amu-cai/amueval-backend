from pydantic import BaseModel


class ChallengeInputModel(BaseModel):
    title: str
    description: str | None = None
    main_metric_parameters: str
    type: str
    main_metric: str
    deadline: str | None = None
    award: str | None = None
    challenge_source: str
    sorting: str
