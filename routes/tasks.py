import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import Task, TaskProgress, User
from routes.login import account_info, current_account, require_admin
from schemas import ISODate, Question, Status, TaskCreate, TaskDifficulty, TaskRead

router = APIRouter()
APP_ZONE = ZoneInfo(os.getenv("TASKFLOW_TIMEZONE", "Asia/Kolkata"))


def today():
    return datetime.now(APP_ZONE).date()


def require_student(account: User = Depends(current_account)):
    if account_info(account)["role"] != "User":
        raise HTTPException(403, "Student access required")
    return account


def progress_student_id(db: Session, account: User, student_id: int | None):
    if account_info(account)["role"] == "User":
        if student_id is not None and student_id != account.id:
            raise HTTPException(403, "You can only view your own progress")
        return account.id

    if student_id is None:
        raise HTTPException(422, "Select a student")

    student = db.get(User, student_id)
    if student is None or student.role.strip().lower() != "user":
        raise HTTPException(404, "Student not found")

    return student.id


def task_view(task: Task, progress: TaskProgress | None):
    return TaskRead(
        id=task.id,
        ques_no=task.ques_no,
        task_date=task.task_date,
        status="Completed" if progress else "Pending",
        difficulty=progress.difficulty if progress else None,
        completed_at=progress.completed_at if progress else None,
        created_at=task.created_at,
    )


def find_tasks(db: Session, student_id: int, task_date=None, status=None):
    query = select(Task, TaskProgress).outerjoin(
        TaskProgress,
        and_(
            TaskProgress.task_id == Task.id,
            TaskProgress.user_id == student_id,
        ),
    )

    if task_date is not None:
        query = query.where(Task.task_date == task_date)

    if status == "Completed":
        query = query.where(TaskProgress.task_id.is_not(None))
    elif status == "Pending":
        query = query.where(TaskProgress.task_id.is_(None))

    rows = db.execute(query.order_by(Task.task_date.desc(), Task.id))
    return [task_view(task, progress) for task, progress in rows]


@router.get("/students", dependencies=[Depends(require_admin)])
def list_students(db: Session = Depends(get_db)):
    students = db.scalars(
        select(User)
        .where(func.lower(func.trim(User.role)) == "user")
        .order_by(User.username, User.id)
    )
    return [
        {"id": student.id, "username": student.username, "email": student.email}
        for student in students
    ]


@router.post("/tasks", response_model=TaskRead, dependencies=[Depends(require_admin)])
def create_task(
    payload: TaskCreate | None = None,
    task_date: ISODate | None = None,
    q_no: Question | None = None,
    db: Session = Depends(get_db),
):
    if payload is None:
        if task_date is None or q_no is None:
            raise HTTPException(422, "Provide task_date and ques_no in the JSON body")
        payload = TaskCreate(task_date=task_date, ques_no=q_no)
    elif task_date is not None or q_no is not None:
        raise HTTPException(422, "Use either JSON or the legacy query parameters")

    task = Task(
        task_date=payload.task_date,
        ques_no=payload.ques_no,
        status="Pending",
        difficulty="",  # Compatible with existing NOT NULL difficulty columns.
        created_at=today(),
    )

    try:
        db.add(task)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Task.id)
            .where(Task.task_date == payload.task_date, Task.ques_no == payload.ques_no)
            .limit(1)
        )
        if existing is not None:
            raise HTTPException(409, "Question already assigned for that date") from None
        raise

    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[TaskRead])
def all_tasks(
    task_date: ISODate | None = None,
    status: Status | None = None,
    student_id: int | None = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    selected = progress_student_id(db, admin, student_id)
    return find_tasks(db, selected, task_date, status)


@router.get("/tasks/today", response_model=list[TaskRead])
def todays_tasks(
    account: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return find_tasks(db, account.id, task_date=today())


@router.get("/tasks/date/{task_date}", response_model=list[TaskRead])
def tasks_by_date(
    task_date: ISODate,
    account: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return find_tasks(db, account.id, task_date=task_date)


@router.get("/calendar/today", dependencies=[Depends(current_account)])
def calendar_today():
    return {"date": today()}


def get_task(db: Session, task_id: int):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


@router.post("/tasks/{task_id}", response_model=TaskRead)
def complete_task(
    task_id: int,
    body: TaskDifficulty,
    account: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    task = get_task(db, task_id)
    progress = TaskProgress(
        user_id=account.id,
        task_id=task_id,
        difficulty=body.difficulty,
        completed_at=today(),
    )

    try:
        with db.begin_nested():
            db.add(progress)
            db.flush()
    except IntegrityError:
        progress = db.get(TaskProgress, (account.id, task_id), with_for_update=True)
        if progress is None:
            raise
        if progress.difficulty != body.difficulty:
            raise HTTPException(
                409, "Task already completed. Use PATCH to change difficulty."
            )

    result = task_view(task, progress)
    db.commit()
    return result


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def change_difficulty(
    task_id: int,
    body: TaskDifficulty,
    account: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    task = get_task(db, task_id)
    progress = db.get(TaskProgress, (account.id, task_id), with_for_update=True)
    if progress is None:
        raise HTTPException(409, "Complete the task before changing its difficulty")

    progress.difficulty = body.difficulty
    result = task_view(task, progress)
    db.commit()
    return result