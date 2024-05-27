from database.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    UnicodeText,
    ForeignKey,
    Float,
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean)
    is_author = Column(Boolean)

    def __repr__(self) -> str:
        return (
            "<User("
            f"id={self.id}, "
            f"username={self.username}, "
            f"email={self.email}, "
            f"hashed_password={self.hashed_password}, "
            f"is_admin={self.is_admin}, "
            f"is_author={self.is_author}"
            ")>"
        )


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    author = Column(String, ForeignKey("users.username"))
    title = Column(String, unique=True)
    source = Column(String)
    type = Column(String)
    description = Column(String)
    main_metric = Column(String)
    main_metric_parameters = Column(String)
    best_score = Column(Float)
    deadline = Column(String)
    award = Column(String)
    readme = Column(UnicodeText)
    deleted = Column(Boolean)
    sorting = Column(String)

    def __repr__(self) -> str:
        return (
            "<Challenge("
            f"id={self.id}, "
            f"author={self.author}, "
            f"title={self.title}, "
            f"source={self.source}, "
            f"type={self.type}, "
            f"description={self.description}, "
            f"main_metric={self.main_metric}, "
            f"main_metric_parameters={self.main_metric_parameters}, "
            f"best_score={self.best_score}, "
            f"deadline={self.deadline}, "
            f"award={self.award}, "
            f"readme={self.readme}, "
            f"deleted={self.deleted}, "
            f"sorting={self.sorting}"
            ")>"
        )


class Submission(Base):
    __tablename__ = "submission"

    id = Column(Integer, primary_key=True, index=True)
    challenge = Column(String, ForeignKey("challenges.title"))
    submitter = Column(String, ForeignKey("users.username"))
    description = Column(String)
    dev_result = Column(Float)
    test_result = Column(Float)
    timestamp = Column(String)
    deleted = Column(Boolean)

    def __repr__(self) -> str:
        return (
            "<Submission("
            f"id={self.id}, "
            f"challenge={self.challenge}, "
            f"submitter={self.submitter}, "
            f"description={self.description}, "
            f"dev_result={self.dev_result}, "
            f"test_result={self.test_result}, "
            f"timestamp={self.timestamp}, "
            f"deleted={self.deleted}"
            ")>"
        )


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    challenge = Column(Integer, ForeignKey("challenges.id"))
    metric = Column(String)
    name = Column(String)
    active = Column(Boolean)

    def __repr__(self) -> str:
        return (
            "<Test("
            f"id={self.id}, "
            f"challenge={self.challenge}, "
            f"metric={self.metric}, "
            f"name={self.name}, "
            f"active={self.active}, "
            ")>"
        )
