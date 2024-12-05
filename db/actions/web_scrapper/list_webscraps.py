from db.schema import Orgnization
from db.index import UserSession
from typing import Annotated
from fastapi import Query
from sqlmodel import select


def list_webscraps(
    session: UserSession,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Orgnization]:
    webscraps = session.exec(select(Orgnization).offset(offset).limit(limit)).all()
    return webscraps
