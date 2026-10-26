# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
La versión del código (`pyproject.toml` y `main.py`) sigue siendo `0.1.0`: la entrada
«Sin publicar» agrupa los cambios que aún no tienen versión asignada.

## [Sin publicar] — 2026-10-25

### Añadido
- `POST /tasks`: registra una tarea con `title`, `due_date` y `priority` y devuelve 201 con
  `id`, `title`, `due_date` y `priority`.
  - `title`: texto de 1 a 120 caracteres tras recortar espacios exteriores; se devuelve normalizado.
  - `due_date`: cadena `YYYY-MM-DD` que sea fecha real. Se rechazan timestamps (numéricos o como
    cadena), fechas con hora y formatos alternativos mediante un validador `before`, porque
    `date` plano los aceptaba y `strict=True` por sí solo rechaza toda cadena a través de FastAPI.
  - `priority`: `TaskPriority(str, Enum)` con `low`, `medium` y `high`.
  - Se rechazan las fechas anteriores a hoy (UTC) con
    `errors.invalid_request("La fecha límite no puede ser anterior a hoy")`; hoy y fechas futuras
    se aceptan. La petición rechazada no guarda la tarea ni consume id.
- Recurso `tasks/` con el patrón de `users/`: `routes.py`, `service.py`, `schemas.py` y
  `repository.py` (almacén en memoria, ids desde 1, sin datos semilla).
- `tests/test_tasks.py`: pruebas de aceptación del endpoint (formato de fecha, límites de título,
  `null` y campos ausentes, prioridades, cambio de día UTC, precedencia de errores, ids tras
  rechazos) y pruebas unitarias de `TaskCreate`, `service.create_task` (con `repository.add`
  sustituido) y `repository`. La fecha actual se fija con `monkeypatch` para que sean deterministas.
- `README.md`: documentación de `POST /tasks`.

### Cambiado
- `main.py` monta el router de `tasks`.
- `tests/conftest.py`: el fixture `_reset_data` reinicia también el repositorio de `tasks`.

### Notas
- Los 422 tienen dos formas de `detail`: lista (errores de Pydantic) o cadena (fecha pasada).
  Los mensajes de Pydantic salen en inglés, igual que en `users`.

### Mantenimiento
- `.gitignore`: se ignoran los archivos de proyecto de PyCharm.

## [0.1.0] — 2026-09-07

### Añadido
- Repo base del Módulo 2: API de usuarios con FastAPI y Pydantic v2 (`GET /health`, `GET /users`,
  `GET /users/{id}`, `POST /users`), almacén en memoria, catálogo de errores en `core/errors.py`
  y suite de tests.
- `README.md`: tabla de ramas por clase (con `solucion-clase1` desde 2026-09-16).

### Corregido
- `core/errors.py` usa `HTTP_422_UNPROCESSABLE_CONTENT`, el nombre no deprecado.
