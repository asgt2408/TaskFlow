from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal,engine
from sqlalchemy.orm import Session
from models import User, Task, Base
from datetime import date

router = APIRouter()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/tasks")
def create_task(task_date: date, q_no: int, db: Session = Depends(get_db)):

    new_task = Task(
        ques_no = q_no,
        task_date = task_date,
        created_at = date.today()
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "task_date" : task_date,
        "ques_no" : q_no,
    }
