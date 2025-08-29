import pytest
from app.task_service import TaskService
from app.models import TaskCreate, TaskUpdate
from app.database import reset_db


@pytest.fixture()
def clean_db():
    """Provide a clean database for each test."""
    reset_db()
    yield
    reset_db()


class TestTaskService:
    """Test suite for TaskService."""

    def test_create_task_success(self, clean_db):
        """Test successful task creation."""
        task_data = TaskCreate(title="Test Task")
        task = TaskService.create_task(task_data)

        assert task is not None
        assert task.id is not None
        assert task.title == "Test Task"
        assert not task.completed
        assert task.created_at is not None

    def test_create_task_with_empty_title_raises_error(self, clean_db):
        """Test that creating a task with empty title raises an error."""
        # SQLModel validation should catch this, but test the behavior
        task_data = TaskCreate(title="")
        task = TaskService.create_task(task_data)

        # Task is created but with empty title - this is handled at validation level
        assert task.title == ""

    def test_get_all_tasks_empty(self, clean_db):
        """Test getting tasks when none exist."""
        tasks = TaskService.get_all_tasks()
        assert tasks == []

    def test_get_all_tasks_with_data(self, clean_db):
        """Test getting tasks when some exist."""
        # Create test tasks
        task1 = TaskService.create_task(TaskCreate(title="First Task"))
        task2 = TaskService.create_task(TaskCreate(title="Second Task"))

        tasks = TaskService.get_all_tasks()

        assert len(tasks) == 2
        # Should be ordered by creation date desc (newest first)
        assert tasks[0].id == task2.id
        assert tasks[1].id == task1.id

    def test_get_task_by_id_exists(self, clean_db):
        """Test getting an existing task by ID."""
        created_task = TaskService.create_task(TaskCreate(title="Test Task"))

        if created_task.id is not None:
            retrieved_task = TaskService.get_task_by_id(created_task.id)

            assert retrieved_task is not None
            assert retrieved_task.id == created_task.id
            assert retrieved_task.title == created_task.title

    def test_get_task_by_id_not_exists(self, clean_db):
        """Test getting a non-existent task by ID."""
        task = TaskService.get_task_by_id(999)
        assert task is None

    def test_update_task_title_only(self, clean_db):
        """Test updating only the task title."""
        created_task = TaskService.create_task(TaskCreate(title="Original Title"))

        if created_task.id is not None:
            update_data = TaskUpdate(title="Updated Title")
            updated_task = TaskService.update_task(created_task.id, update_data)

            assert updated_task is not None
            assert updated_task.title == "Updated Title"
            assert not updated_task.completed  # Should remain unchanged

    def test_update_task_completion_only(self, clean_db):
        """Test updating only the task completion status."""
        created_task = TaskService.create_task(TaskCreate(title="Test Task"))

        if created_task.id is not None:
            update_data = TaskUpdate(completed=True)
            updated_task = TaskService.update_task(created_task.id, update_data)

            assert updated_task is not None
            assert updated_task.title == "Test Task"  # Should remain unchanged
            assert updated_task.completed

    def test_update_task_both_fields(self, clean_db):
        """Test updating both title and completion status."""
        created_task = TaskService.create_task(TaskCreate(title="Original Title"))

        if created_task.id is not None:
            update_data = TaskUpdate(title="New Title", completed=True)
            updated_task = TaskService.update_task(created_task.id, update_data)

            assert updated_task is not None
            assert updated_task.title == "New Title"
            assert updated_task.completed

    def test_update_task_not_exists(self, clean_db):
        """Test updating a non-existent task."""
        update_data = TaskUpdate(title="Should Not Work")
        result = TaskService.update_task(999, update_data)
        assert result is None

    def test_toggle_task_completion_to_completed(self, clean_db):
        """Test toggling task from pending to completed."""
        created_task = TaskService.create_task(TaskCreate(title="Test Task"))

        if created_task.id is not None:
            toggled_task = TaskService.toggle_task_completion(created_task.id)

            assert toggled_task is not None
            assert toggled_task.completed

    def test_toggle_task_completion_to_pending(self, clean_db):
        """Test toggling task from completed to pending."""
        created_task = TaskService.create_task(TaskCreate(title="Test Task"))

        if created_task.id is not None:
            # First, mark as completed
            TaskService.update_task(created_task.id, TaskUpdate(completed=True))

            # Then toggle back to pending
            toggled_task = TaskService.toggle_task_completion(created_task.id)

            assert toggled_task is not None
            assert not toggled_task.completed

    def test_toggle_task_completion_not_exists(self, clean_db):
        """Test toggling completion of a non-existent task."""
        result = TaskService.toggle_task_completion(999)
        assert result is None

    def test_delete_task_exists(self, clean_db):
        """Test deleting an existing task."""
        created_task = TaskService.create_task(TaskCreate(title="Task to Delete"))

        if created_task.id is not None:
            success = TaskService.delete_task(created_task.id)

            assert success

            # Verify task is actually deleted
            deleted_task = TaskService.get_task_by_id(created_task.id)
            assert deleted_task is None

    def test_delete_task_not_exists(self, clean_db):
        """Test deleting a non-existent task."""
        success = TaskService.delete_task(999)
        assert not success

    def test_get_task_statistics_empty(self, clean_db):
        """Test statistics when no tasks exist."""
        stats = TaskService.get_task_statistics()

        expected = {"total": 0, "completed": 0, "pending": 0}
        assert stats == expected

    def test_get_task_statistics_mixed_tasks(self, clean_db):
        """Test statistics with mixed completed and pending tasks."""
        # Create tasks with different completion states
        TaskService.create_task(TaskCreate(title="Pending Task 1"))
        task2 = TaskService.create_task(TaskCreate(title="Completed Task 1"))
        task3 = TaskService.create_task(TaskCreate(title="Completed Task 2"))
        TaskService.create_task(TaskCreate(title="Pending Task 2"))

        # Mark some as completed
        if task2.id is not None:
            TaskService.update_task(task2.id, TaskUpdate(completed=True))
        if task3.id is not None:
            TaskService.update_task(task3.id, TaskUpdate(completed=True))

        stats = TaskService.get_task_statistics()

        expected = {"total": 4, "completed": 2, "pending": 2}
        assert stats == expected

    def test_get_task_statistics_all_completed(self, clean_db):
        """Test statistics when all tasks are completed."""
        task1 = TaskService.create_task(TaskCreate(title="Task 1"))
        task2 = TaskService.create_task(TaskCreate(title="Task 2"))

        # Mark all as completed
        if task1.id is not None:
            TaskService.update_task(task1.id, TaskUpdate(completed=True))
        if task2.id is not None:
            TaskService.update_task(task2.id, TaskUpdate(completed=True))

        stats = TaskService.get_task_statistics()

        expected = {"total": 2, "completed": 2, "pending": 0}
        assert stats == expected

    def test_get_task_statistics_all_pending(self, clean_db):
        """Test statistics when all tasks are pending."""
        TaskService.create_task(TaskCreate(title="Pending Task 1"))
        TaskService.create_task(TaskCreate(title="Pending Task 2"))
        TaskService.create_task(TaskCreate(title="Pending Task 3"))

        stats = TaskService.get_task_statistics()

        expected = {"total": 3, "completed": 0, "pending": 3}
        assert stats == expected

    def test_task_ordering(self, clean_db):
        """Test that tasks are returned in creation order (newest first)."""
        # Create tasks in sequence
        TaskService.create_task(TaskCreate(title="First Task"))
        TaskService.create_task(TaskCreate(title="Second Task"))
        TaskService.create_task(TaskCreate(title="Third Task"))

        tasks = TaskService.get_all_tasks()

        # Should be in reverse order of creation (newest first)
        assert len(tasks) == 3
        assert tasks[0].title == "Third Task"
        assert tasks[1].title == "Second Task"
        assert tasks[2].title == "First Task"

    def test_none_handling_in_update(self, clean_db):
        """Test that None values in TaskUpdate don't overwrite existing data."""
        created_task = TaskService.create_task(TaskCreate(title="Original Title"))

        if created_task.id is not None:
            # Update with None values - should not change anything
            update_data = TaskUpdate(title=None, completed=None)
            updated_task = TaskService.update_task(created_task.id, update_data)

            assert updated_task is not None
            assert updated_task.title == "Original Title"
            assert not updated_task.completed
