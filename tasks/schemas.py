"""Schemas Pydantic del recurso `tasks`.

Las rutas devuelven siempre estos modelos (vía `response_model=`), nunca `dict`
crudos. El modelo de entrada termina en `Create`.
"""
from datetime import date
from enum import Enum

from pydantic import BaseModel


class TaskPriority(str, Enum):
    """Prioridades permitidas, en minúsculas exactas."""

    low = "low"
    medium = "medium"
    high = "high"


class TaskBase(BaseModel):
    title: str
    due_date: date
    priority: TaskPriority


class TaskCreate(TaskBase):
    """Cuerpo de entrada para crear una tarea."""

    # TODO: redeclarar title con StringConstraints(strip_whitespace=True,
    #       min_length=1, max_length=120). Solo aquí, no en TaskBase.
    # TODO: field_validator("due_date", mode="before"): solo cadena YYYY-MM-DD (ASCII).
    #       Solo aquí: en Task rechazaría el objeto `date` al construir la salida.


class Task(TaskBase):
    """Tarea tal como la devuelve la API."""

    id: int
