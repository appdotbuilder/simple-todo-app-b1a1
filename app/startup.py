from app.database import create_tables
import app.todo_app


def startup() -> None:
    # this function is called before the first request
    create_tables()
    app.todo_app.create()
