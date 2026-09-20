from fastapi import FastAPI
from routes.signup import router as signup_router
from routes.login import router as login_router
from routes.tasks import router as tasks_router

app = FastAPI()

app.include_router(signup_router)
app.include_router(login_router)
app.include_router(tasks_router)

