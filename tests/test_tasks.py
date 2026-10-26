"""Tests del recurso `tasks`.

Mismo estilo que test_users.py: un test por caso, nombres descriptivos en español,
arrange / act / assert separados por una línea en blanco.

Notas del contrato:
  - Los 422 de Pydantic llevan `detail` como lista; el 422 de fecha pasada (service)
    lleva `detail` como cadena.
  - No se afirma el texto de `msg` de Pydantic (sale en inglés): solo `loc` y `type`.
  - `id == 1` se comprueba solo donde prueba generación o consumo de IDs.
"""
from datetime import datetime, timezone

import pytest

from tasks import service

RELOJ_BASE = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


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


# TODO: tests (cada uno con su caso feliz o de error; números = tabla del plan)
#
# --- Caso feliz e IDs ---
# test_create_task_devuelve_201_y_la_tarea                  (#1; id == 1)
# test_create_task_asigna_ids_consecutivos                  (ids 1 y 2)
# test_create_task_acepta_cada_prioridad                    (#22; parametrizado; sin id)
# test_create_task_normaliza_espacios_exteriores            (#2, #7)
#
# --- title ---
# test_create_task_titulo_invalido_devuelve_422             (#3, #4, #6, #8; parametrizado)
# test_create_task_titulo_de_120_caracteres_devuelve_201    (#5)
#
# --- Campos null y ausentes ---
# test_create_task_campo_null_devuelve_422(campo)           (status + loc)
# test_create_task_campo_ausente_devuelve_422(campo)        (type == "missing" + loc)
#   campo: title, priority (pendiente decidir si se añade due_date)
#
# --- due_date: formato (422 de Pydantic) ---
# test_create_task_fecha_con_formato_invalido_devuelve_422  (#14-#20; loc == ["body", "due_date"])
#
# --- due_date: regla de negocio y reloj ---
# test_create_task_fecha_de_ayer_devuelve_422_con_mensaje   (#10; detail es cadena exacta)
# test_create_task_fecha_de_hoy_y_manana_devuelve_201       (#11, #12)
# test_create_task_fecha_bisiesta_valida_devuelve_201       (#13; futura respecto al reloj base)
# test_create_task_cambio_de_dia_utc                        (#26-#29; usa fijar_ahora(instante))
#
# --- priority ---
# test_create_task_prioridad_invalida_devuelve_422          (#23; parametrizado)
#
# --- Prioridad de errores ---
# test_create_task_fecha_pasada_con_prioridad_invalida_devuelve_422_de_pydantic
#   (#32; detail es lista, loc apunta a priority)
#
# --- Estructura y persistencia ---
# test_create_task_cuerpo_vacio_devuelve_422                (#25)
# test_create_task_rechazo_de_dominio_no_consume_id         (422, luego válida con id == 1)
# test_create_task_rechazo_de_pydantic_no_consume_id        (422, luego válida con id == 1)
# test_create_task_ignora_campos_extra                      (el campo extra no se devuelve)
