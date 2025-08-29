import logging
from nicegui import ui
from app.task_service import TaskService
from app.models import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


def create():
    """Create the todo application UI."""

    # Apply modern theme
    ui.colors(
        primary="#2563eb",  # Professional blue
        secondary="#64748b",  # Subtle gray
        accent="#10b981",  # Success green
        positive="#10b981",
        negative="#ef4444",  # Error red
        warning="#f59e0b",  # Warning amber
        info="#3b82f6",  # Info blue
    )

    @ui.page("/")
    def todo_page():
        """Main todo application page."""

        # Page header
        with ui.row().classes("w-full justify-between items-center mb-8"):
            ui.label("Todo Application").classes("text-3xl font-bold text-gray-800")
            ui.button("Refresh", icon="refresh", on_click=lambda: refresh_tasks()).classes("px-4 py-2")

        # Statistics cards
        stats_container = ui.row().classes("gap-4 w-full mb-6")

        # Task input form
        with ui.card().classes("w-full p-6 shadow-lg rounded-lg mb-6"):
            ui.label("Add New Task").classes("text-xl font-semibold text-gray-700 mb-4")

            with ui.row().classes("gap-4 w-full items-end"):
                task_input = ui.input(placeholder="Enter your task...").classes("flex-1")

                ui.button("Add Task", icon="add", on_click=lambda: add_task()).classes(
                    "bg-primary text-white px-6 py-2"
                )

        # Tasks list container
        tasks_container = ui.column().classes("w-full gap-2")

        def create_statistics_cards():
            """Create or update statistics cards."""
            stats_container.clear()
            stats = TaskService.get_task_statistics()

            with stats_container:
                # Total tasks card
                with ui.card().classes("p-4 bg-white shadow-md rounded-xl hover:shadow-lg transition-shadow"):
                    ui.label("Total Tasks").classes("text-sm text-gray-500 uppercase tracking-wider")
                    ui.label(str(stats["total"])).classes("text-2xl font-bold text-gray-800 mt-1")

                # Completed tasks card
                with ui.card().classes("p-4 bg-white shadow-md rounded-xl hover:shadow-lg transition-shadow"):
                    ui.label("Completed").classes("text-sm text-gray-500 uppercase tracking-wider")
                    ui.label(str(stats["completed"])).classes("text-2xl font-bold text-green-600 mt-1")

                # Pending tasks card
                with ui.card().classes("p-4 bg-white shadow-md rounded-xl hover:shadow-lg transition-shadow"):
                    ui.label("Pending").classes("text-sm text-gray-500 uppercase tracking-wider")
                    ui.label(str(stats["pending"])).classes("text-2xl font-bold text-orange-600 mt-1")

        def create_task_item(task):
            """Create a task item UI component."""

            # Task card styling based on completion status
            card_classes = "p-4 shadow-md rounded-lg hover:shadow-lg transition-all duration-200"
            if task.completed:
                card_classes += " bg-green-50 border-l-4 border-green-400"
            else:
                card_classes += " bg-white border-l-4 border-blue-400"

            with ui.card().classes(card_classes):
                with ui.row().classes("w-full items-center justify-between"):
                    # Task content
                    with ui.row().classes("flex-1 items-center gap-3"):
                        # Completion checkbox
                        def make_toggle_handler(task_id: int | None):
                            def handler(e):
                                if task_id is not None:
                                    toggle_task_completion(task_id)

                            return handler

                        ui.checkbox(value=task.completed, on_change=make_toggle_handler(task.id)).classes(
                            "text-primary"
                        )

                        # Task title with strikethrough for completed tasks
                        title_classes = "text-lg flex-1"
                        if task.completed:
                            title_classes += " line-through text-gray-500"
                        else:
                            title_classes += " text-gray-800"

                        ui.label(task.title).classes(title_classes)

                        # Created date
                        created_date = task.created_at.strftime("%Y-%m-%d %H:%M")
                        ui.label(f"Created: {created_date}").classes("text-sm text-gray-500")

                    # Action buttons
                    with ui.row().classes("gap-2"):
                        # Edit button
                        def make_edit_handler(task_id: int | None):
                            async def handler():
                                if task_id is not None:
                                    await edit_task_dialog(task_id)

                            return handler

                        ui.button(icon="edit", on_click=make_edit_handler(task.id)).classes("p-2").props(
                            "flat round color=primary"
                        )

                        # Delete button
                        def make_delete_handler(task_id: int | None):
                            async def handler():
                                if task_id is not None:
                                    await confirm_delete_task(task_id)

                            return handler

                        ui.button(icon="delete", on_click=make_delete_handler(task.id)).classes("p-2").props(
                            "flat round color=negative"
                        )

        def refresh_tasks():
            """Refresh the tasks list and statistics."""
            with tasks_container:
                tasks_container.clear()

            create_statistics_cards()

            tasks = TaskService.get_all_tasks()

            with tasks_container:
                if not tasks:
                    with ui.card().classes("p-8 text-center bg-gray-50 rounded-lg"):
                        ui.icon("inbox", size="4em").classes("text-gray-400 mb-4")
                        ui.label("No tasks yet").classes("text-xl text-gray-600 mb-2")
                        ui.label("Add your first task above to get started!").classes("text-gray-500")
                else:
                    for task in tasks:
                        create_task_item(task)

        def add_task():
            """Add a new task."""
            title = task_input.value
            if not title or not title.strip():
                ui.notify("Please enter a task title", type="warning")
                return

            try:
                TaskService.create_task(TaskCreate(title=title.strip()))
                task_input.set_value("")
                refresh_tasks()
                ui.notify("Task added successfully!", type="positive")
            except Exception as e:
                logger.error(f"Error adding task: {str(e)}")
                ui.notify(f"Error adding task: {str(e)}", type="negative")

        def toggle_task_completion(task_id: int):
            """Toggle task completion status."""
            if task_id is None:
                ui.notify("Invalid task ID", type="warning")
                return

            try:
                updated_task = TaskService.toggle_task_completion(task_id)
                if updated_task:
                    status = "completed" if updated_task.completed else "pending"
                    ui.notify(f"Task marked as {status}", type="positive")
                    refresh_tasks()
                else:
                    ui.notify("Task not found", type="warning")
            except Exception as e:
                logger.error(f"Error updating task: {str(e)}")
                ui.notify(f"Error updating task: {str(e)}", type="negative")

        async def edit_task_dialog(task_id: int):
            """Show edit task dialog."""
            if task_id is None:
                ui.notify("Invalid task ID", type="warning")
                return

            task = TaskService.get_task_by_id(task_id)
            if task is None:
                ui.notify("Task not found", type="warning")
                return

            with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
                ui.label("Edit Task").classes("text-xl font-semibold mb-4")

                # Title input
                ui.label("Task Title").classes("text-sm font-medium text-gray-700 mb-1")
                title_input = ui.input(value=task.title).classes("w-full mb-4")

                # Completion status
                ui.label("Status").classes("text-sm font-medium text-gray-700 mb-1")
                completed_checkbox = ui.checkbox("Completed", value=task.completed).classes("mb-4")

                # Action buttons
                with ui.row().classes("gap-2 justify-end w-full"):
                    ui.button("Cancel", on_click=lambda: dialog.submit("cancel")).props("outline")
                    ui.button("Save", on_click=lambda: dialog.submit("save")).classes("bg-primary text-white")

            result = await dialog

            if result == "save":
                new_title = title_input.value
                if not new_title or not new_title.strip():
                    ui.notify("Please enter a task title", type="warning")
                    return

                try:
                    update_data = TaskUpdate(title=new_title.strip(), completed=completed_checkbox.value)
                    updated_task = TaskService.update_task(task_id, update_data)
                    if updated_task:
                        ui.notify("Task updated successfully!", type="positive")
                        refresh_tasks()
                    else:
                        ui.notify("Task not found", type="warning")
                except Exception as e:
                    logger.error(f"Error updating task: {str(e)}")
                    ui.notify(f"Error updating task: {str(e)}", type="negative")

        async def confirm_delete_task(task_id: int):
            """Show delete confirmation dialog."""
            if task_id is None:
                ui.notify("Invalid task ID", type="warning")
                return

            task = TaskService.get_task_by_id(task_id)
            if task is None:
                ui.notify("Task not found", type="warning")
                return

            with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
                ui.label("Delete Task").classes("text-xl font-semibold mb-4")
                ui.label(f'Are you sure you want to delete "{task.title}"?').classes("mb-4")
                ui.label("This action cannot be undone.").classes("text-sm text-gray-500 mb-6")

                with ui.row().classes("gap-2 justify-end w-full"):
                    ui.button("Cancel", on_click=lambda: dialog.submit("cancel")).props("outline")
                    ui.button("Delete", on_click=lambda: dialog.submit("delete")).classes("bg-red-500 text-white")

            result = await dialog

            if result == "delete":
                try:
                    success = TaskService.delete_task(task_id)
                    if success:
                        ui.notify("Task deleted successfully!", type="positive")
                        refresh_tasks()
                    else:
                        ui.notify("Task not found", type="warning")
                except Exception as e:
                    logger.error(f"Error deleting task: {str(e)}")
                    ui.notify(f"Error deleting task: {str(e)}", type="negative")

        # Handle Enter key in task input
        task_input.on("keydown.enter", lambda: add_task())

        # Initial load
        refresh_tasks()
