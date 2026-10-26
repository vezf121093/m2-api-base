"""Schemas Pydantic del recurso `tasks`.

Las rutas devuelven siempre estos modelos (vía `response_model=`), nunca `dict`
crudos. El modelo de entrada termina en `Create`.
"""
import re
from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


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

    # Las reglas de entrada van solo aquí, no en TaskBase: el validador de due_date
    # rechazaría el objeto `date` al construir la salida `Task`.
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]

    @field_validator("due_date", mode="before")
    @classmethod
    def _require_iso_date_string(cls, value: object) -> object:
        """Solo una cadena YYYY-MM-DD; `date` por sí solo aceptaría timestamps y fechas con hora."""
        if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
            raise ValueError("La fecha límite debe ser una cadena con formato YYYY-MM-DD")
        return value


class Task(TaskBase):
    """Tarea tal como la devuelve la API."""

    id: int
