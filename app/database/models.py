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
    deadline = Column(String)
    award = Column(String)
    deleted = Column(Boolean)

    def __repr__(self) -> str:
        return (
            "<Challenge("
            f"id={self.id}, "
            f"author={self.author}, "
            f"title={self.title}, "
            f"source={self.source}, "
            f"type={self.type}, "
            f"description={self.description}, "
            f"deadline={self.deadline}, "
            f"award={self.award}, "
            f"deleted={self.deleted}, "
            ")>"
        )


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    challenge = Column(Integer, ForeignKey("challenges.id"))
    submitter = Column(Integer, ForeignKey("users.id"))
    description = Column(String)
    timestamp = Column(String)
    deleted = Column(Boolean)

    def __repr__(self) -> str:
        return (
            "<Submission("
            f"id={self.id}, "
            f"challenge={self.challenge}, "
            f"submitter={self.submitter}, "
            f"description={self.description}, "
            f"time_stamp={self.timestamp}, "
            f"deleted={self.deleted}"
            ")>"
        )


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    challenge = Column(Integer, ForeignKey("challenges.id"))
    metric = Column(String)
    metric_parameters = Column(String)
    main_metric = Column(Boolean)
    active = Column(Boolean)

    def __repr__(self) -> str:
        return (
            "<Test("
            f"id={self.id}, "
            f"challenge={self.challenge}, "
            f"metric={self.metric}, "
            f"metric_parameters={self.metric_parameters}, "
            f"main_metric={self.main_metric}, "
            f"active={self.active}"
            ")>"
        )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    test = Column(Integer, ForeignKey("tests.id"))
    submission = Column(Integer, ForeignKey("submissions.id"))
    score = Column(Float)
    timestamp = Column(String)

    def __repr__(self) -> str:
        return (
            "<Evaluation("
            f"id={self.id}, "
            f"test={self.test}, "
            f"submission={self.submission}, "
            f"score={self.score}, "
            f"time_stamp={self.timestamp}"
            ")>"
        )
