import pandas as pd
import streamlit as st

from api_client import api

DIFFICULTIES = ["Easy", "Medium", "Hard"]


def metrics(total, completed):
    columns = st.columns(3)
    columns[0].metric("Total questions", total)
    columns[1].metric("Completed", completed)
    columns[2].metric("Pending", total - completed)


def task_metrics(tasks):
    completed = sum(task["status"] == "Completed" for task in tasks)
    metrics(len(tasks), completed)
    return completed


def task_table(tasks):
    if not tasks:
        st.info("No tasks match this view.")
        return

    labels = {
        "ques_no": "Question",
        "task_date": "Assigned",
        "status": "Status",
        "difficulty": "Difficulty",
        "completed_at": "Completed on",
    }
    table = pd.DataFrame(tasks)[list(labels)].rename(columns=labels)
    st.dataframe(table, hide_index=True, width="stretch")


def analytics_view(admin=False, student_id=None):
    params = {"student_id": student_id} if student_id is not None else {}
    data = api("GET", "/analytics", params=params)
    if data is None:
        return

    metrics(data["total_tasks"], data["completed_tasks"])
    percentage = data["completion_percentage"]
    st.progress(percentage / 100, text=f"{percentage:.2f}% complete")

    if data["total_tasks"] == 0:
        st.info("Analytics will appear after questions are assigned.")
        return

    st.subheader("Completed by difficulty")
    breakdown = pd.DataFrame({
        "Difficulty": DIFFICULTIES,
        "Completed": [data[f"{level.lower()}_completed"] for level in DIFFICULTIES],
    })
    st.bar_chart(breakdown, x="Difficulty", y="Completed")

    if admin:
        st.subheader("Completion by assigned date")
        assigned = pd.DataFrame(data["by_assignment_date"])
        assigned["date"] = pd.to_datetime(assigned["date"])
        st.line_chart(assigned, x="date", y=["assigned", "completed"])

    st.subheader("Recent completions")
    as_of = pd.Timestamp(data["as_of"])
    week_start = as_of - pd.Timedelta(days=as_of.weekday())
    periods = (
        ("Last 14 days", "daily_completions", "date", pd.date_range(end=as_of, periods=14)),
        (
            "Last 8 weeks", "weekly_completions", "week",
            pd.date_range(end=week_start, periods=8, freq="W-MON"),
        ),
    )

    for column, (label, key, date_key, index) in zip(st.columns(2), periods):
        by_period = {
            pd.Timestamp(row[date_key]): row["completed"] for row in data[key]
        }
        series = pd.Series(by_period, dtype=int).reindex(index, fill_value=0)
        column.write(label)
        column.bar_chart(series.rename("Completed"), x_label=label, y_label="Questions")

    if not admin and data["daily_completions"]:
        st.subheader("Progress over time")
        daily = pd.DataFrame(data["daily_completions"])
        daily["date"] = pd.to_datetime(daily["date"])
        daily["Total solved"] = daily["completed"].cumsum()
        st.line_chart(daily, x="date", y="Total solved")
