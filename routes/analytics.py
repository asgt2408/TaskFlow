from collections import Counter, defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from routes.login import current_account
from routes.tasks import find_tasks, progress_student_id, today

router = APIRouter()


@router.get("/analytics")
def analytics(
    student_id: int | None = None,
    account: User = Depends(current_account),
    db: Session = Depends(get_db),
):
    selected = progress_student_id(db, account, student_id)

    assignments = defaultdict(lambda: {"assigned": 0, "completed": 0})
    daily = Counter()
    weekly = Counter()
    difficulty = Counter()
    total = completed = 0

    for task in reversed(find_tasks(db, selected)):
        total += 1
        assignments[task.task_date]["assigned"] += 1

        if task.status == "Completed":
            completed += 1
            assignments[task.task_date]["completed"] += 1
            if task.difficulty:
                difficulty[task.difficulty] += 1
            if task.completed_at:
                day = task.completed_at
                daily[day] += 1
                weekly[day - timedelta(days=day.weekday())] += 1

    return {
        "as_of": today(),
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": total - completed,
        "completion_percentage": round(100 * completed / total, 2) if total else 0.0,
        "easy_completed": difficulty["Easy"],
        "medium_completed": difficulty["Medium"],
        "hard_completed": difficulty["Hard"],
        "by_assignment_date": [
            {"date": day, **counts} for day, counts in assignments.items()
        ],
        "daily_completions": [
            {"date": day, "completed": count} for day, count in sorted(daily.items())
        ],
        "weekly_completions": [
            {"week": week, "completed": count} for week, count in sorted(weekly.items())
        ],
    }