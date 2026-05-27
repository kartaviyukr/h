# Нейромаркет

Кросс-платформенное приложение: персональное меню под цели пользователя (LLM),
подбор рецептов через RAG, коррекция КБЖУ, сравнение цен между сервисами доставки
в РФ и формирование корзины с дип-линками.

> Текущая стадия: **Фаза 1** — скелет монорепо (Flutter «Hello», FastAPI `/health`,
> локальная БД, CI). Бизнес-логика добавляется в последующих фазах.

## Структура

```
apps/mobile      # Flutter-клиент (Android/iOS/Web/Desktop)
services/api     # FastAPI backend
db/init          # init-скрипты PostgreSQL (расширение pgvector)
docs/            # планы по фазам
```

## Требования
- Docker + Docker Compose
- Python 3.11 (для запуска API без докера)
- Flutter SDK 3.x (для запуска клиента)

## Быстрый запуск (API + БД)

```bash
docker compose up --build
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

API-документация: http://localhost:8000/docs

## Запуск API без Docker

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Тесты и линт бэкенда:

```bash
cd services/api
ruff check .
pytest
```

## Запуск Flutter-клиента

```bash
cd apps/mobile
flutter pub get
flutter run        # выбери устройство (web/android/ios/desktop)
```

Тесты и анализ клиента:

```bash
cd apps/mobile
flutter analyze
flutter test
```

## Секреты
Все секреты — через `.env` (см. `services/api/.env.example`). Файл `.env`
**не коммитится** (см. `.gitignore`).
