# Нейромаркет

Кросс-платформенное приложение: персональное меню под цели пользователя (LLM),
подбор рецептов через RAG, коррекция КБЖУ, сравнение цен между сервисами доставки
в РФ и формирование корзины с дип-линками.

> Текущая стадия: **Фаза 2** — аутентификация (email/пароль + Google ID-token)
> и профиль пользователя (цели КБЖУ, антропометрия, аллергии, бюджет).
> Миграции — Alembic. Фронтенд-экраны — в отдельной фазе.

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

Контейнер `api` при старте прогоняет миграции (`alembic upgrade head`).

API-документация: http://localhost:8000/docs

### Auth и профиль (Фаза 2)

```bash
# регистрация → токен
curl -s -XPOST localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"a@b.com","password":"secret123"}'

# профиль (нужен Bearer-токен)
curl -s localhost:8000/profile -H "Authorization: Bearer <token>"
```

Эндпоинты: `POST /auth/register`, `POST /auth/login`, `POST /auth/google`
(приём Google ID-token), `GET /auth/me`, `GET|PUT /profile`.

## Запуск API без Docker

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://neuromarket:neuromarket@localhost:5432/neuromarket
export JWT_SECRET=dev-secret
alembic upgrade head
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
