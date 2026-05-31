from pathlib import Path
from typing import Self
from sqlmodel import Session, create_engine
from sqlalchemy import Engine


class UnitOfWork:
    def __init__(self, engine: Engine = create_engine(f"sqlite:///{Path(__file__).parent / "test.db"}")):
        self.engine = engine

    def __enter__(self) -> Self:
        self.session = Session(bind=self.engine, expire_on_commit=False)
        return self

    @property
    def command(self):
        from .command import CommandRepository
        return CommandRepository(session=self.session)

    @property
    def query(self):
        from .query import QueryRepository
        return QueryRepository(session=self.session)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
