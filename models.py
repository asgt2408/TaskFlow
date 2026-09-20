from database import Base
from sqlalchemy import Column, Integer, String, Date

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100),nullable=False)
    email = Column(String(100),unique=True,nullable=False)
    password = Column(String(500),nullable=False)
    role  = Column(String(50),nullable=False)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    ques_no = Column(String(100), nullable=False)
    task_date = Column(Date, nullable=False)
    status = Column(String(50), default="NULL", nullable=False)
    difficulty = Column(String(50), default="NULL", nullable=False)
    completed_at = Column(Date, default="NULL", nullable=True)
    created_at = Column(Date, nullable=True)

