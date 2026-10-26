"""Almacén en memoria del recurso `tasks`.

Sustituye a una base de datos real para que el proyecto sea ejecutable sin
infraestructura. Sin datos semilla: el primer ID es 1.
"""
from datetime import date

from tasks.schemas import Task, TaskPriority

_tasks: dict[int, Task] = {}
_next_id: int = 1


def add(*, title: str, due_date: date, priority: TaskPriority) -> Task:
    """Guarda una tarea nueva con el siguiente ID y la devuelve."""
    global _next_id
    task = Task(id=_next_id, title=title, due_date=due_date, priority=priority)
    _tasks[task.id] = task
    _next_id += 1
    return task


def reset() -> None:
    """Deja el almacén vacío y el contador en 1. Se usa entre tests."""
    global _next_id
    _tasks.clear()
    _next_id = 1
