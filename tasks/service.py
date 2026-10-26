"""Lógica de negocio del recurso `tasks`.

Las rutas no acceden al repositorio directamente: pasan por aquí. Esta capa es la
única que conoce `repository.py` y la que decide cuándo algo es un error de
dominio (usando `core.errors`).
"""
from datetime import date, datetime, timezone  # noqa: F401  # TODO: se usan al implementar

from core import errors  # noqa: F401  # TODO: se usa al implementar
from tasks import repository  # noqa: F401  # TODO: se usa al implementar
from tasks.schemas import Task, TaskCreate


def create_task(data: TaskCreate) -> Task:
    """Crea una tarea si la fecha límite no es anterior a hoy (UTC).

    Lanza `errors.invalid_request("La fecha límite no puede ser anterior a hoy")`
    si `data.due_date` es anterior a `datetime.now(timezone.utc).date()`. En ese
    caso no guarda nada.
    """
    # TODO: calcular hoy en UTC, comparar, rechazar o llamar a repository.add(...)
    raise NotImplementedError
