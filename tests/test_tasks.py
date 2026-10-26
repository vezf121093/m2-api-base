"""Tests del recurso `tasks`.

Mismo estilo que test_users.py: un test por caso, nombres descriptivos en español,
arrange / act / assert separados por una línea en blanco.

Notas del contrato:
  - Los 422 de Pydantic llevan `detail` como lista; el 422 de fecha pasada (service)
    lleva `detail` como cadena.
  - No se afirma el texto de `msg` de Pydantic (sale en inglés): solo `loc` y `type`.
  - `id == 1` se comprueba solo donde prueba generación o consumo de IDs.
"""
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import Response
from pydantic import ValidationError

from tasks import repository, service
from tasks.schemas import Task, TaskCreate, TaskPriority

RELOJ_BASE = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
MENSAJE_FECHA_PASADA = "La fecha límite no puede ser anterior a hoy"


@pytest.fixture
def fijar_ahora(monkeypatch: pytest.MonkeyPatch):
    """Fija el instante que ve `tasks.service`. `monkeypatch` lo revierte al terminar el test."""

    def _fijar(instante: datetime) -> None:
        class _Fijo(datetime):
            @classmethod
            def now(cls, tz=None):
                assert tz is not None, "el service debe pasar timezone a now()"
                return instante.astimezone(tz)

        monkeypatch.setattr(service, "datetime", _Fijo)

    return _fijar


@pytest.fixture(autouse=True)
def _reloj_base(fijar_ahora) -> None:
    """Ningún test toca el reloj real: hoy = 2026-10-24 (UTC) salvo que el test lo cambie."""
    fijar_ahora(RELOJ_BASE)


def _cuerpo(**cambios: object) -> dict[str, object]:
    """Cuerpo válido de referencia; cada test sobreescribe solo lo que le interesa."""
    cuerpo: dict[str, object] = {
        "title": "Comprar café",
        "due_date": "2026-10-25",
        "priority": "medium",
    }
    cuerpo.update(cambios)
    return cuerpo


def _errores_de_pydantic(response: Response) -> list[dict]:
    """`detail` de un 422 de Pydantic: siempre una lista de errores."""
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    return detail


# --- Caso feliz e IDs ---


def test_create_task_devuelve_201_y_la_tarea(client: TestClient) -> None:
    response = client.post("/tasks", json=_cuerpo())

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "Comprar café",
        "due_date": "2026-10-25",
        "priority": "medium",
    }


def test_create_task_asigna_ids_consecutivos(client: TestClient) -> None:
    primera = client.post("/tasks", json=_cuerpo(title="Primera"))
    segunda = client.post("/tasks", json=_cuerpo(title="Segunda"))

    assert primera.json()["id"] == 1
    assert segunda.json()["id"] == 2


@pytest.mark.parametrize("prioridad", ["low", "medium", "high"])
def test_create_task_acepta_cada_prioridad(client: TestClient, prioridad: str) -> None:
    response = client.post("/tasks", json=_cuerpo(priority=prioridad))

    assert response.status_code == 201
    assert response.json()["priority"] == prioridad


@pytest.mark.parametrize(
    ("enviado", "esperado"),
    [
        pytest.param("  Hola  ", "Hola", id="espacios_exteriores"),
        pytest.param(" " + "x" * 120 + " ", "x" * 120, id="120_mas_espacios_exteriores"),
        pytest.param("  a   b  ", "a   b", id="espacios_internos_se_conservan"),
    ],
)
def test_create_task_normaliza_espacios_exteriores(
    client: TestClient, enviado: str, esperado: str
) -> None:
    response = client.post("/tasks", json=_cuerpo(title=enviado))

    assert response.status_code == 201
    assert response.json()["title"] == esperado


# --- title ---


@pytest.mark.parametrize(
    "titulo",
    [
        pytest.param("   ", id="solo_espacios"),
        pytest.param("", id="vacio"),
        pytest.param("x" * 121, id="121_caracteres"),
        pytest.param(123, id="numero"),
    ],
)
def test_create_task_titulo_invalido_devuelve_422(client: TestClient, titulo: object) -> None:
    response = client.post("/tasks", json=_cuerpo(title=titulo))

    assert response.status_code == 422
    errores = _errores_de_pydantic(response)
    assert [error["loc"] for error in errores] == [["body", "title"]]


def test_create_task_titulo_de_120_caracteres_devuelve_201(client: TestClient) -> None:
    response = client.post("/tasks", json=_cuerpo(title="x" * 120))

    assert response.status_code == 201
    assert len(response.json()["title"]) == 120


# --- Campos null y ausentes ---


@pytest.mark.parametrize("campo", ["title", "priority", "due_date"])
def test_create_task_campo_null_devuelve_422(client: TestClient, campo: str) -> None:
    response = client.post("/tasks", json=_cuerpo(**{campo: None}))

    assert response.status_code == 422
    errores = _errores_de_pydantic(response)
    assert [error["loc"] for error in errores] == [["body", campo]]


@pytest.mark.parametrize("campo", ["title", "priority", "due_date"])
def test_create_task_campo_ausente_devuelve_422(client: TestClient, campo: str) -> None:
    cuerpo = _cuerpo()
    del cuerpo[campo]

    response = client.post("/tasks", json=cuerpo)

    assert response.status_code == 422
    errores = _errores_de_pydantic(response)
    assert [(error["loc"], error["type"]) for error in errores] == [(["body", campo], "missing")]


# --- due_date: formato (422 de Pydantic) ---


@pytest.mark.parametrize(
    "fecha",
    [
        pytest.param("2027-02-29", id="29_feb_en_año_no_bisiesto"),
        pytest.param("2026-02-30", id="30_feb"),
        pytest.param(1729728000, id="timestamp_numerico"),
        pytest.param("1729728000", id="timestamp_como_cadena"),
        pytest.param("2026-10-25T00:00:00", id="fecha_con_hora_cero"),
        pytest.param("2026-10-25T10:30:00", id="fecha_con_hora"),
        pytest.param("2026-10-25T10:30:00Z", id="fecha_con_hora_y_zona"),
        pytest.param("20261025", id="sin_separadores"),
        pytest.param("25/10/2026", id="formato_dia_mes_año"),
        pytest.param("2026-1-5", id="sin_ceros"),
        pytest.param(" 2026-10-25", id="espacio_inicial"),
    ],
)
def test_create_task_fecha_con_formato_invalido_devuelve_422(
    client: TestClient, fecha: object
) -> None:
    response = client.post("/tasks", json=_cuerpo(due_date=fecha))

    assert response.status_code == 422
    errores = _errores_de_pydantic(response)
    assert [error["loc"] for error in errores] == [["body", "due_date"]]


# --- due_date: regla de negocio y reloj ---


def test_create_task_fecha_de_ayer_devuelve_422_con_mensaje(client: TestClient) -> None:
    response = client.post("/tasks", json=_cuerpo(due_date="2026-10-23"))

    assert response.status_code == 422
    assert response.json() == {"detail": MENSAJE_FECHA_PASADA}


@pytest.mark.parametrize("fecha", ["2026-10-24", "2026-10-25"], ids=["hoy", "manana"])
def test_create_task_fecha_de_hoy_y_manana_devuelve_201(client: TestClient, fecha: str) -> None:
    response = client.post("/tasks", json=_cuerpo(due_date=fecha))

    assert response.status_code == 201
    assert response.json()["due_date"] == fecha


def test_create_task_fecha_bisiesta_valida_devuelve_201(client: TestClient) -> None:
    # Con el reloj base (24-oct-2026) esta fecha es futura: no activa la regla de fecha pasada.
    response = client.post("/tasks", json=_cuerpo(due_date="2028-02-29"))

    assert response.status_code == 201
    assert response.json()["due_date"] == "2028-02-29"


@pytest.mark.parametrize(
    ("instante", "fecha", "status_esperado"),
    [
        pytest.param(
            datetime(2026, 10, 24, 23, 59, 59, tzinfo=timezone.utc),
            "2026-10-24",
            201,
            id="justo_antes_del_cambio_de_dia_utc",
        ),
        pytest.param(
            datetime(2026, 10, 25, 0, 0, 0, tzinfo=timezone.utc),
            "2026-10-24",
            422,
            id="justo_despues_del_cambio_de_dia_utc",
        ),
        pytest.param(
            datetime(2026, 10, 24, 20, 0, tzinfo=timezone(timedelta(hours=-5))),
            "2026-10-24",
            422,
            id="hora_local_aun_24_pero_utc_ya_25",
        ),
        pytest.param(
            datetime(2026, 10, 25, 0, 30, tzinfo=timezone(timedelta(hours=2))),
            "2026-10-24",
            201,
            id="hora_local_ya_25_pero_utc_aun_24",
        ),
    ],
)
def test_create_task_cambio_de_dia_utc(
    client: TestClient, fijar_ahora, instante: datetime, fecha: str, status_esperado: int
) -> None:
    fijar_ahora(instante)

    response = client.post("/tasks", json=_cuerpo(due_date=fecha))

    assert response.status_code == status_esperado
    if status_esperado == 422:
        assert response.json() == {"detail": MENSAJE_FECHA_PASADA}


# --- priority ---


@pytest.mark.parametrize(
    "prioridad",
    [
        pytest.param("urgent", id="valor_desconocido"),
        pytest.param("LOW", id="mayusculas"),
        pytest.param("High", id="capitalizado"),
        pytest.param("", id="vacio"),
        pytest.param(1, id="numero"),
    ],
)
def test_create_task_prioridad_invalida_devuelve_422(
    client: TestClient, prioridad: object
) -> None:
    response = client.post("/tasks", json=_cuerpo(priority=prioridad))

    assert response.status_code == 422
    errores = _errores_de_pydantic(response)
    assert [error["loc"] for error in errores] == [["body", "priority"]]


# --- Prioridad de errores ---


def test_create_task_fecha_pasada_con_prioridad_invalida_devuelve_422_de_pydantic(
    client: TestClient,
) -> None:
    response = client.post("/tasks", json=_cuerpo(due_date="2026-10-23", priority="urgent"))

    assert response.status_code == 422
    errores = _errores_de_pydantic(response)  # lista, no la cadena del service
    assert [error["loc"] for error in errores] == [["body", "priority"]]


# --- Estructura y persistencia ---


def test_create_task_cuerpo_vacio_devuelve_422(client: TestClient) -> None:
    response = client.post("/tasks", json={})

    assert response.status_code == 422
    errores = _errores_de_pydantic(response)
    assert {error["type"] for error in errores} == {"missing"}
    assert {tuple(error["loc"]) for error in errores} == {
        ("body", "title"),
        ("body", "due_date"),
        ("body", "priority"),
    }


def test_create_task_rechazo_de_dominio_no_consume_id(client: TestClient) -> None:
    rechazada = client.post("/tasks", json=_cuerpo(due_date="2026-10-23"))

    valida = client.post("/tasks", json=_cuerpo())

    assert rechazada.status_code == 422
    assert valida.status_code == 201
    assert valida.json()["id"] == 1


def test_create_task_rechazo_de_pydantic_no_consume_id(client: TestClient) -> None:
    rechazada = client.post("/tasks", json=_cuerpo(title="   "))

    valida = client.post("/tasks", json=_cuerpo())

    assert rechazada.status_code == 422
    assert valida.status_code == 201
    assert valida.json()["id"] == 1


def test_create_task_ignora_campos_extra(client: TestClient) -> None:
    response = client.post("/tasks", json=_cuerpo(extra="no debe devolverse"))

    assert response.status_code == 201
    assert "extra" not in response.json()


# =====================================================================================
# Pruebas unitarias
#
# Prueban cada capa por separado, sin pasar por HTTP. No repiten la tabla de casos del
# endpoint: solo lo que cada capa decide por sí misma. El estado del repositorio lo
# reinicia el fixture autouse de conftest.py (llama a `tasks.repository.reset()`).
# =====================================================================================


# --- schemas: TaskCreate ---


def test_task_create_normaliza_el_titulo() -> None:
    datos = {"title": "  Hola   mundo  ", "due_date": "2026-10-25", "priority": "low"}

    tarea = TaskCreate(**datos)

    assert tarea.title == "Hola   mundo"


def test_task_create_convierte_la_fecha_valida_en_date() -> None:
    datos = {"title": "Tarea", "due_date": "2026-10-25", "priority": "low"}

    tarea = TaskCreate(**datos)

    assert tarea.due_date == date(2026, 10, 25)


@pytest.mark.parametrize(
    "fecha",
    [
        pytest.param("2026-10-25T10:30:00", id="fecha_con_hora"),
        pytest.param("1729728000", id="timestamp_como_cadena"),
        pytest.param(1729728000, id="timestamp_numerico"),
    ],
)
def test_task_create_rechaza_fecha_con_formato_invalido(fecha: object) -> None:
    datos = {"title": "Tarea", "due_date": fecha, "priority": "low"}

    with pytest.raises(ValidationError) as excinfo:
        TaskCreate(**datos)

    assert [error["loc"] for error in excinfo.value.errors()] == [("due_date",)]


# --- service: create_task ---


@pytest.fixture
def llamadas_a_add(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """Sustituye `repository.add` por un doble que registra los argumentos que recibe."""
    llamadas: list[dict[str, object]] = []

    def _add_falso(**campos: object) -> Task:
        llamadas.append(campos)
        return Task(id=99, **campos)

    monkeypatch.setattr(repository, "add", _add_falso)
    return llamadas


def test_create_task_con_fecha_pasada_no_intenta_guardar(
    llamadas_a_add: list[dict[str, object]],
) -> None:
    datos = TaskCreate(title="Tarea", due_date="2026-10-23", priority="low")

    with pytest.raises(HTTPException) as excinfo:
        service.create_task(datos)

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == MENSAJE_FECHA_PASADA
    assert llamadas_a_add == []


def test_create_task_con_fecha_de_hoy_guarda_con_los_datos_normalizados(
    llamadas_a_add: list[dict[str, object]],
) -> None:
    datos = TaskCreate(title="  Tarea  ", due_date="2026-10-24", priority="high")

    tarea = service.create_task(datos)

    assert llamadas_a_add == [
        {"title": "Tarea", "due_date": date(2026, 10, 24), "priority": TaskPriority.high}
    ]
    assert tarea.id == 99  # lo devuelto por el doble: el service no crea la tarea por su cuenta


# --- repository: add / reset ---


def _agregar(titulo: str) -> Task:
    return repository.add(title=titulo, due_date=date(2026, 10, 25), priority=TaskPriority.low)


def test_add_asigna_ids_consecutivos() -> None:
    primera = _agregar("Primera")

    segunda = _agregar("Segunda")

    assert (primera.id, segunda.id) == (1, 2)


def test_add_guarda_las_tareas() -> None:
    primera = _agregar("Primera")
    segunda = _agregar("Segunda")

    guardadas = repository._tasks

    assert guardadas == {1: primera, 2: segunda}


def test_reset_vacia_el_almacen_y_reinicia_los_ids() -> None:
    _agregar("Antigua")

    repository.reset()
    nueva = _agregar("Nueva")

    assert nueva.id == 1
    assert repository._tasks == {1: nueva}
