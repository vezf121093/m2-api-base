# m2-api-base

API REST de usuarios usada como base en el **Módulo 2 · Clase 1 — Generación de código con IA**.

Es un proyecto pequeño pero completo: tiene convenciones, capas separadas, catálogo
de errores y una suite de tests que pasa. Le falta **una** feature — la que vas a
construir en el laboratorio.

## Requisitos

- Python 3.10 o superior
- (Recomendado) Claude Code instalado

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
uvicorn main:app --reload          # http://127.0.0.1:8000  ·  Swagger en /docs
```

Endpoints actuales:

| Método | Ruta              | Descripción                     |
|--------|-------------------|---------------------------------|
| GET    | `/health`         | Estado del servicio             |
| GET    | `/users`          | Lista de usuarios               |
| GET    | `/users/{id}`     | Un usuario por id (404 si no existe) |
| POST   | `/users`          | Crea un usuario (409 si el email ya existe) |
| POST   | `/tasks`          | Registra una tarea con fecha límite y prioridad (422 si es inválida) |

### `POST /tasks`

Cuerpo JSON (los tres campos son obligatorios y no aceptan `null`):

| Campo      | Regla |
|------------|-------|
| `title`    | Texto. Se recortan los espacios exteriores y debe tener entre 1 y 120 caracteres. Se devuelve normalizado; los espacios internos se conservan. |
| `due_date` | Cadena `YYYY-MM-DD` que sea una fecha real. Se rechazan timestamps, fechas con hora y otros formatos. Debe ser hoy o futura, según la fecha **UTC**. |
| `priority` | `low`, `medium` o `high`, en minúsculas. |

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "  Comprar café  ", "due_date": "2026-10-30", "priority": "medium"}'
# 201 → {"id": 1, "title": "Comprar café", "due_date": "2026-10-30", "priority": "medium"}
```

Los errores devuelven **422** con dos formas de `detail`:

- Estructura, tipos o formato (Pydantic): `detail` es una **lista** de errores con `loc` y `type`.
  Los mensajes los genera Pydantic, en inglés.
- Fecha pasada (regla de negocio de `tasks/service.py`): `detail` es una **cadena**,
  `{"detail": "La fecha límite no puede ser anterior a hoy"}`.

Si una petición trae ambos problemas, prevalece el 422 de Pydantic. Una petición
rechazada no guarda la tarea ni consume un id. Los ids empiezan en 1 (no hay datos semilla)
y el almacén es en memoria, como el de `users`. Los campos extra del cuerpo se ignoran.

## Tests y calidad

```bash
pytest                                       # correr la suite
pytest --cov=. --cov-report=term-missing     # con cobertura
ruff check .                                 # linter
```

## Ramas del módulo

`main` es la base de la **Clase 1**. Cada clase tiene su rama de trabajo y su
rama de solución:

| Clase | Rama de trabajo | Solución | Qué añade |
|-------|-----------------|----------|-----------|
| 1 · Generación | `main` | `solucion-clase1` | La base. Falta `GET /users/search`. |
| 2 · Testing | `clase2-testing` | `solucion-clase2` | `users/validation.py` sin tests → llévalo a >80%. |
| 3 · Debugging | `clase3-debugging` | `solucion-clase3` | Recurso `reports/` con 3 bugs plantados. |
| 4 · Review | `clase4-review` | `solucion-clase4` | PR de `GET /reports/export` con issues (verde). |

```bash
git switch clase2-testing     # o la que toque
```

## Tarea del laboratorio (Clase 1)

Añadir `GET /users/search?email=<email>`:

- **200** con el usuario si existe
- **422** si el formato del email es inválido
- **404** si no hay ningún usuario con ese email
- con su test en `tests/test_users.py`, siguiendo el estilo del archivo

Lee `CLAUDE.md` antes de empezar: ahí están las convenciones que tu código debe respetar.
