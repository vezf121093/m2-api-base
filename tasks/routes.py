"""Rutas HTTP del recurso `tasks`.

Sin lógica de negocio: la función delega en `service.py`.
"""
from fastapi import APIRouter, status

from tasks import service
from tasks.schemas import Task, TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate) -> Task:
    return service.create_task(data)
