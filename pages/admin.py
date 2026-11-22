from datetime import date

import streamlit as st

from api_client import api
from dashboard import analytics_view, task_metrics, task_table

st.title("Admin dashboard")
section = st.sidebar.radio("Admin", ["Add task", "Task status", "Analytics"])
st.header(section)

if section != "Add task":
    students = api("GET", "/students")
    if students is None:
        st.stop()
    if not students:
        st.info("Add a student account to view progress.")
        st.stop()

    labels = {
        student["id"]: f"{student['username']} ({student['email']})"
        for student in students
    }
    student_id = st.selectbox(
        "Student",
        list(labels),
        format_func=labels.__getitem__,
    )

if section == "Add task":
    calendar = api("GET", "/calendar/today")
    if calendar is not None:
        with st.form("add_task"):
            assigned_date = st.date_input("Assign for", date.fromisoformat(calendar["date"]))
            question = st.text_input("Question identifier", max_chars=100)
            submitted = st.form_submit_button("Add task", type="primary")

        if submitted:
            if not question.strip():
                st.warning("Enter a question identifier.")
            else:
                task = api(
                    "POST",
                    "/tasks",
                    json={"task_date": assigned_date.isoformat(), "ques_no": question.strip()},
                )
                if task is not None:
                    st.success(f"Assigned {task['ques_no']} for {task['task_date']}.")

elif section == "Task status":
    date_column, status_column = st.columns(2)
    assigned_date = date_column.date_input("Assigned date", value=None)
    status = status_column.selectbox("Status", ["All", "Pending", "Completed"])

    filters = {"student_id": student_id}
    if assigned_date:
        filters["task_date"] = assigned_date.isoformat()
    if status != "All":
        filters["status"] = status

    tasks = api("GET", "/tasks", params=filters)
    if tasks is not None:
        task_metrics(tasks)
        task_table(tasks)

else:
    analytics_view(admin=True, student_id=student_id)
