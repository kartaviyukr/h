# Нейромаркет

Кросс-платформенное приложение: персональное меню под цели пользователя (LLM),
подбор рецептов через RAG, коррекция КБЖУ, сравнение цен между сервисами доставки
в РФ и формирование корзины с дип-линками.

> Текущая стадия: **Фаза 6** — формирование корзины из сравнения цен и
> per-item дип-линки на товары провайдера (агрегированный URL — заглушка под
> боевые билдеры). Ранее: Фаза 2 — auth/профиль, Фаза 3 — меню (DeepSeek),
> Фаза 4 — RAG по рецептам, Фаза 5 — сравнение цен. Боевые адаптеры конкретных
> сервисов (Самокат/СберМаркет/Лавка/ВкусВилл) и фронтенд-экраны — последующие фазы.

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

### Меню (Фаза 3)

Генерация персонального меню через DeepSeek по профилю. Требуется
`DEEPSEEK_API_KEY` в `.env` и исходящий доступ к `api.deepseek.com`.

```bash
# сгенерировать меню (нужен Bearer-токен)
curl -s -XPOST localhost:8000/menu/generate \
  -H "Authorization: Bearer <token>" -H 'content-type: application/json' \
  -d '{"days_count":3,"include_snacks":true}'
```

Эндпоинты: `POST /menu/generate`, `GET /menu` (история), `GET /menu/{id}`.
КБЖУ корректируется под цель из профиля масштабированием граммовок.

### RAG по рецептам (Фаза 4)

Меню «приземляется» на корпус рецептов: при генерации из профиля строится
запрос, top-k похожих рецептов передаются DeepSeek как основа. Если индекс пуст
или недоступен — генерация работает как в Фазе 3 (fallback).

Эмбеддинги — локальные (`sentence-transformers`), поэтому ингестия выносится в
отдельный шаг и требует extra `[rag]` и доступа в интернет:

```bash
cd services/api
pip install -e ".[rag]"
# заполни data/recipe_seeds.txt URL-ами страниц рецептов (schema.org Recipe)
python -m app.scripts.ingest_recipes --source data/recipe_seeds.txt
```

Параметры в `.env`: `RAG_ENABLED`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`, `RAG_TOP_K`.

### Сравнение цен (Фаза 5)

По ингредиентам меню оцениваем стоимость корзины у каждого включённого
провайдера и выбираем самого дешёвого. Стоимость считается по целым упаковкам
(параметр `proportional` включает пропорциональный режим).

```bash
# посчитать и сохранить сравнение
curl -s -XPOST localhost:8000/menu/<menu_id>/prices \
  -H "Authorization: Bearer <token>" -H 'content-type: application/json' \
  -d '{}'

# последнее сравнение
curl -s localhost:8000/menu/<menu_id>/prices -H "Authorization: Bearer <token>"
```

Каталог демо-провайдеров — `services/api/data/price_catalog.json`. Параметры
в `.env`: `PRICE_CATALOG_PATH`, `PRICE_PROVIDERS` (фильтр по кодам).

### Корзина и дип-линки (Фаза 6)

По меню и сохранённому сравнению цен собирается корзина у выбранного провайдера
(по умолчанию — самый дешёвый). Per-item URLs берутся из товара (`ProductOffer.url`);
агрегированная ссылка на корзину — `null` в v1 (приходит с боевыми билдерами).

```bash
# создать корзину (provider опционален: по умолчанию cheapest_provider)
curl -s -XPOST localhost:8000/menu/<menu_id>/cart \
  -H "Authorization: Bearer <token>" -H 'content-type: application/json' \
  -d '{}'

# последняя корзина меню
curl -s localhost:8000/menu/<menu_id>/cart -H "Authorization: Bearer <token>"

# конкретная корзина
curl -s localhost:8000/cart/<cart_id> -H "Authorization: Bearer <token>"
```

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
