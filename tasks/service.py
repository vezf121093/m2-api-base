"""Lógica de negocio del recurso `tasks`.

Las rutas no acceden al repositorio directamente: pasan por aquí. Esta capa es la
única que conoce `repository.py` y la que decide cuándo algo es un error de
dominio (usando `core.errors`).
"""
from datetime import datetime, timezone

from core import errors
from tasks import repository
from tasks.schemas import Task, TaskCreate


def create_task(data: TaskCreate) -> Task:
    """Crea una tarea si la fecha límite no es anterior a hoy (UTC).

    Lanza `errors.invalid_request("La fecha límite no puede ser anterior a hoy")`
    si `data.due_date` es anterior a `datetime.now(timezone.utc).date()`. En ese
    caso no guarda nada.
    """
    if data.due_date < datetime.now(timezone.utc).date():
        raise errors.invalid_request("La fecha límite no puede ser anterior a hoy")
    return repository.add(title=data.title, due_date=data.due_date, priority=data.priority)
