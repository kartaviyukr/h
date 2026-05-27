# Фаза 2 — План: Auth + профиль пользователя

> Статус: **ожидает подтверждения**. Код не пишется до утверждения этого плана.

## ⚠️ Отклонение от зафиксированного стека (согласовано)
В ТЗ значился **Supabase Auth (email + OAuth Google)**. По согласованию в Фазе 2
делаем **собственную email/пароль аутентификацию на FastAPI** (свой выпуск JWT,
хеш паролей bcrypt). Это сознательное отклонение, зафиксировано здесь.
- Профиль и пользователи — в **нашей** PostgreSQL (не в Supabase).
- **Google OAuth** своими силами заметно тяжелее (redirect-флоу, client secret).
  Предлагаю в Фазе 2 сделать только email/пароль, а Google OAuth вынести в
  отдельную мини-фазу/PR. См. «Открытые вопросы».

## Цель фазы
- Регистрация и вход по email+паролю, выпуск и валидация JWT.
- Таблицы `users` и `profiles` в Postgres, миграции через Alembic.
- CRUD профиля (цели КБЖУ, антропометрия+цель, аллергии/исключения, бюджет).
- Защищённые эндпоинты (только владелец видит/меняет свой профиль).
- Тесты (pytest) на auth и профиль. Flutter в этой фазе **не трогаем**
  (экраны логина/профиля — отдельная фаза UI, если не решим иначе).

## Слои (по архитектурным принципам)
```
api/         роуты (auth, profile)
services/    бизнес-логика (AuthService, ProfileService)
repositories/ доступ к БД (UserRepository, ProfileRepository)
core/        config, security (хеш/JWT), зависимости (get_current_user)
db/          engine/session, базовый класс моделей
```

## Структура файлов (дополнения к services/api)
```
services/api/
├── app/
│   ├── core/
│   │   ├── config.py            # + JWT_SECRET, JWT_EXPIRE_MINUTES, ALGORITHM
│   │   ├── security.py          # bcrypt hash/verify, create/decode JWT
│   │   └── deps.py              # get_db, get_current_user (Bearer)
│   ├── db/
│   │   ├── base.py              # DeclarativeBase
│   │   └── session.py           # engine, SessionLocal, get_session
│   ├── models/
│   │   ├── user.py              # User (id, email, password_hash, created_at)
│   │   └── profile.py           # Profile (FK user_id, поля ниже)
│   ├── schemas/
│   │   ├── auth.py              # RegisterIn, LoginIn, TokenOut
│   │   └── profile.py          # ProfileIn, ProfileOut, ProfileUpdate
│   ├── repositories/
│   │   ├── user_repo.py
│   │   └── profile_repo.py
│   ├── services/
│   │   ├── auth_service.py
│   │   └── profile_service.py
│   └── api/
│       ├── auth.py             # POST /auth/register, /auth/login, GET /auth/me
│       └── profile.py         # GET/PUT /profile
├── alembic/                    # окружение миграций
│   ├── env.py
│   └── versions/
├── alembic.ini
└── tests/
    ├── test_auth.py
    └── test_profile.py
```

## Стек / зависимости (добавляем в pyproject.toml)
- `sqlalchemy>=2.0` (ORM, async или sync — предлагаю **sync** для простоты старта).
- `alembic` (миграции).
- `psycopg[binary]` (драйвер Postgres).
- `passlib[bcrypt]` (хеш паролей) или `bcrypt` напрямую.
- `pyjwt` (JWT) — или `python-jose`. Предлагаю **pyjwt** (легче).
- `email-validator` (валидация email в Pydantic).
- dev: `pytest`, `httpx` (уже есть).
- Тесты БД: SQLite в памяти не подойдёт из-за pgvector/типов — используем
  Postgres из docker-compose, либо `testcontainers`/отдельная тестовая схема.
  Предлагаю: тесты гоняют против Postgres из compose (в CI — service-контейнер).

## Модель данных

### users
| поле | тип | примечание |
|------|-----|-----------|
| id | UUID PK | `gen_random_uuid()` |
| email | citext/text UNIQUE | нормализуем lower |
| password_hash | text | bcrypt |
| created_at | timestamptz | default now() |

### profiles (1:1 с users)
| поле | тип | примечание |
|------|-----|-----------|
| user_id | UUID PK/FK → users.id | on delete cascade |
| display_name | text NULL | имя |
| sex | enum(male/female) NULL | для расчёта |
| age | int NULL | |
| height_cm | int NULL | |
| weight_kg | numeric NULL | |
| activity_level | enum NULL | sedentary…very_active |
| goal | enum NULL | lose/maintain/gain |
| target_kcal | int NULL | целевые калории/день |
| target_protein_g | int NULL | |
| target_fat_g | int NULL | |
| target_carbs_g | int NULL | |
| allergies | text[] | аллергены/исключения (рус.) |
| budget_rub | numeric NULL | |
| budget_period | enum NULL | week/month |
| updated_at | timestamptz | |

Комментарии к колонкам с пользовательскими данными — на русском (по правилам).
Авто-расчёт КБЖУ из антропометрии (Mifflin-St Jeor) — **опционально**, как хелпер
в `profile_service`; пользователь может задать цели вручную (поля nullable).

## Эндпоинты
- `POST /auth/register` — {email, password} → создаёт user + пустой profile, возвращает токен.
- `POST /auth/login` — {email, password} → {access_token, token_type}.
- `GET  /auth/me` — текущий пользователь (по Bearer).
- `GET  /profile` — профиль текущего пользователя.
- `PUT  /profile` — обновить поля профиля (partial update).

Авторизация: `Authorization: Bearer <jwt>`; `get_current_user` декодит JWT,
достаёт user_id, грузит пользователя. 401 при невалидном/просроченном токене.

## Безопасность
- Пароли — только bcrypt-хеш, минимальная длина пароля (напр. ≥8).
- JWT_SECRET — из `.env` (добавим в `.env.example`, пустой).
- Не отдаём `password_hash` наружу никогда.
- Профиль строго привязан к токену — пользователь не может читать чужой.

## Миграции (Alembic)
- Инициализируем `alembic/`, `env.py` берёт `DATABASE_URL` из settings и
  metadata из `app.db.base`.
- Первая миграция: `users`, `profiles`, нужные enum-типы.
- README дополним: `alembic upgrade head`; в docker-compose — прогон миграций
  при старте api (entrypoint или отдельная команда).

## CI
- В job `backend` добавляем Postgres как service-контейнер (`pgvector/pgvector:pg15`),
  прогоняем `alembic upgrade head` перед `pytest`.

## Тесты
- Регистрация → 200 + токен; повторный email → 409.
- Логин верный/неверный пароль → 200/401.
- `/auth/me` без токена → 401, с токеном → 200.
- `GET/PUT /profile`: дефолт пустой, partial update, нельзя получить чужой.

## Вне рамок Фазы 2
- Flutter-экраны логина/профиля (предлагаю отдельной UI-фазой).
- Генерация меню (Фаза 3).
- Google OAuth (см. открытый вопрос).
- Сброс пароля, подтверждение email, refresh-токены — позже при необходимости.

## Решения (подтверждено)
1. **Google OAuth** — включаем в Фазу 2.
2. **SQLAlchemy** — sync.
3. **JWT** — pyjwt (`pyjwt[crypto]` для RS256 при проверке Google-токенов).
4. **Тестовая БД** — Postgres-сервис (compose/CI service), без SQLite.
5. **Flutter UI** — вне Фазы 2 (только бэкенд).

## Google OAuth — дизайн (backend-only, без redirect-флоу)
Клиент (позже) получает **Google ID token** через нативный Google Sign-In и шлёт
его на бэк. Бэк проверяет токен и выпускает наш JWT. Redirect-флоу и client secret
на сервере не нужны.
- `POST /auth/google` — body `{id_token}`.
- Проверка в `app/integrations/google_oauth.py`: подпись по Google JWKS
  (`https://www.googleapis.com/oauth2/v3/certs`, через `PyJWKClient`),
  `aud == GOOGLE_CLIENT_ID`, `iss in {accounts.google.com, https://accounts.google.com}`.
- Из токена берём `email` и `sub` (Google user id).
- find-or-create: если есть user с таким `google_sub` или `email` — логиним,
  иначе создаём (password_hash NULL). Возвращаем наш `TokenOut`.
- Поля users: `password_hash` **nullable**, добавляем `google_sub text UNIQUE NULL`.
- `.env`: `GOOGLE_CLIENT_ID` (в `.env.example`, пустой).
- Тесты: мокаем верификатор Google (без реального сетевого вызова).

После подтверждения реализую один PR: модели+миграции, auth (email/пароль +
Google), профиль, тесты; прогоню ruff и (где возможно) pytest.
