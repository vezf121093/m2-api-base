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
    # TODO: construir Task con _next_id, guardarla en _tasks, incrementar _next_id.
    raise NotImplementedError


def reset() -> None:
    """Deja el almacén vacío y el contador en 1. Se usa entre tests."""
    global _next_id
    _tasks.clear()
    _next_id = 1
