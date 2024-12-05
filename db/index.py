from sqlmodel import create_engine, SQLModel, Session
from fastapi import Depends 
import os
from dotenv import load_dotenv
from typing import Annotated
from llm.ChatHistory import ChatHistory
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        session.chat_history = ChatHistory()
        yield session

UserSession = Annotated[Session, Depends(get_session)]
