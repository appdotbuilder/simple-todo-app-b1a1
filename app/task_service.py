from typing import Optional
from sqlmodel import select
from app.database import get_session
from app.models import Task, TaskCreate, TaskUpdate


class TaskService:
    """Service layer for task management operations."""

    @staticmethod
    def create_task(task_data: TaskCreate) -> Task:
        """Create a new task."""
        with get_session() as session:
            task = Task(title=task_data.title)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    @staticmethod
    def get_all_tasks() -> list[Task]:
        """Get all tasks ordered by creation date (newest first)."""
        with get_session() as session:
            from sqlmodel import desc

            statement = select(Task).order_by(desc(Task.created_at))
            return list(session.exec(statement).all())

    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Task]:
        """Get a task by its ID."""
        with get_session() as session:
            return session.get(Task, task_id)

    @staticmethod
    def update_task(task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        """Update an existing task."""
        with get_session() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None

            # Update only provided fields
            if task_update.title is not None:
                task.title = task_update.title
            if task_update.completed is not None:
                task.completed = task_update.completed

            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    @staticmethod
    def toggle_task_completion(task_id: int) -> Optional[Task]:
        """Toggle the completion status of a task."""
        with get_session() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None

            task.completed = not task.completed
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    @staticmethod
    def delete_task(task_id: int) -> bool:
        """Delete a task. Returns True if successful, False if task not found."""
        with get_session() as session:
            task = session.get(Task, task_id)
            if task is None:
                return False

            session.delete(task)
            session.commit()
            return True

    @staticmethod
    def get_task_statistics() -> dict[str, int]:
        """Get statistics about tasks."""
        with get_session() as session:
            all_tasks = list(session.exec(select(Task)).all())
            total = len(all_tasks)
            completed = sum(1 for task in all_tasks if task.completed)
            pending = total - completed

            return {"total": total, "completed": completed, "pending": pending}
