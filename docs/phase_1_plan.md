# Фаза 1 — План: Скелет монорепо

> Статус: **ожидает подтверждения**. Код не пишется до утверждения этого плана.

## Цель фазы
Поднять каркас монорепозитория, который локально запускается одной командой:
- базовый Flutter-проект с одним экраном «Hello»;
- базовый FastAPI с эндпоинтом `/health`;
- локальная БД PostgreSQL 15 + pgvector через `docker-compose`;
- CI на GitHub Actions (линт + тесты для бэка и фронта);
- `README` с инструкциями запуска.

Бизнес-логики (меню, RAG, доставка) в этой фазе **нет** — только скелет и инфраструктура.

## Структура репозитория
```
.
├── apps/
│   └── mobile/                 # Flutter-приложение (один экран «Hello»)
│       ├── lib/
│       │   └── main.dart
│       ├── test/
│       │   └── widget_test.dart
│       └── pubspec.yaml
├── services/
│   └── api/                    # FastAPI backend
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py         # создание приложения, подключение роутов
│       │   ├── core/
│       │   │   └── config.py   # Pydantic Settings, чтение .env
│       │   └── api/
│       │       └── health.py   # GET /health
│       ├── tests/
│       │   └── test_health.py
│       ├── pyproject.toml      # зависимости + конфиг ruff/pytest
│       ├── Dockerfile
│       └── .env.example
├── docker-compose.yml          # postgres+pgvector, api
├── .github/
│   └── workflows/
│       └── ci.yml              # линт + тесты (backend + flutter)
├── docs/
│   └── phase_1_plan.md
├── .gitignore
└── README.md
```

## Backend (services/api)
- Python 3.11, FastAPI, Pydantic v2, Uvicorn.
- Менеджер зависимостей: **pip + pyproject.toml** (PEP 621). Без Poetry, чтобы не плодить инструменты; при желании позже перейдём на uv.
- `GET /health` → `{"status": "ok", "version": "<app_version>"}`.
- `core/config.py`: `Settings` (pydantic-settings) с полями под будущее (`database_url`, `deepseek_api_key` и т.п.), читает из `.env`. В Фазе 1 используется минимально.
- Линтер/форматтер: **ruff** (lint + format).
- Тесты: **pytest** + `httpx`/`TestClient` — проверка `/health` → 200.
- Dockerfile: `python:3.11-slim`, установка зависимостей, запуск uvicorn.

## Frontend (apps/mobile)
- Flutter 3.x, один экран «Hello» (`MaterialApp` + `Scaffold` + центрированный текст).
- Riverpod уже добавляем в зависимости (`flutter_riverpod`) и оборачиваем `ProviderScope`, но без провайдеров — задел на Фазу 2.
- Тест: `flutter_test` — виджет-тест, что текст «Hello» отображается.
- Линт: `flutter_lints` (стандартный `analysis_options.yaml`).
- Примечание: сам Flutter SDK я в контейнере не разворачиваю; проект создаётся по стандартной структуре, локальная сборка — на стороне разработчика (инструкции в README).

## База данных
- Образ: `pgvector/pgvector:pg15` (Postgres 15 с расширением pgvector).
- В Фазе 1 — только поднятие контейнера, расширение `vector` создаётся init-скриптом (`CREATE EXTENSION IF NOT EXISTS vector;`). Миграций и таблиц пока нет (появятся в Фазе 2 с профилем пользователя).
- Подключение к Supabase в проде — позже; локально работаем с этим контейнером.

## docker-compose
- Сервис `db` (pgvector/pg15), порт 5432, volume для данных, init-скрипт расширения.
- Сервис `api` (build из `services/api`), порт 8000, зависит от `db`, переменные из `.env`.
- Команда запуска всего стека: `docker compose up --build`.

## CI (GitHub Actions)
Один workflow `ci.yml`, два job:
1. **backend**: setup Python 3.11 → install → `ruff check` → `pytest`.
2. **flutter**: `subosito/flutter-action` → `flutter pub get` → `flutter analyze` → `flutter test`.
Триггеры: push и pull_request.

## README
- Что за проект (кратко).
- Требования: Docker, Flutter SDK, Python 3.11.
- Запуск бэка+БД: `docker compose up --build`, проверка `curl localhost:8000/health`.
- Локальный запуск API без докера (venv).
- Запуск Flutter: `cd apps/mobile && flutter run`.
- Где лежит `.env.example`, что секреты не коммитим.

## .gitignore / секреты
- Игнор: `.env`, `__pycache__/`, `.venv/`, Flutter `build/`, `.dart_tool/`, и т.п.
- `.env.example` с пустыми значениями (DATABASE_URL, DEEPSEEK_API_KEY и пр.).

## Вне рамок Фазы 1
- Auth, профиль пользователя — Фаза 2.
- LLM, RAG, провайдеры доставки — последующие фазы.
- Деплой на Fly.io/Railway/Supabase — позже (сейчас только локальный запуск).

## Открытые вопросы (нужно подтверждение)
1. **Менеджер зависимостей Python**: предлагаю `pip + pyproject.toml`. Ок, или предпочитаешь Poetry/uv?
2. **Имя пакета приложения Flutter** (`name` в pubspec): предлагаю `neuromarket`. Подходит?
3. **Версионирование**: начинаем с `0.1.0` для обоих проектов — ок?

После твоего «ок» приступлю к реализации скелета по этой структуре, прогоню линтеры/тесты и закоммичу одним PR.
