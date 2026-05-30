# Фаза 7 — План: Flutter-клиент (UI поверх бэкенда)

> Статус: **ожидает подтверждения**. Код не пишется до утверждения этого плана.

## Цель фазы
Поднять Flutter-клиент с экранами, покрывающими готовый API: вход/регистрация,
профиль, генерация и просмотр меню, сравнение цен, корзина с открытием
дип-линков. Без лишней косметики — рабочий каркас с понятной навигацией.

## ⚠️ Ограничения окружения
В этом контейнере **нет Flutter SDK** и закрыт PyPI/CDN — собрать/запустить
приложение здесь нельзя. Пишу код и виджет-тесты, валидирую `flutter analyze`
и `flutter test` в **CI** (workflow Фазы 1 уже это делает). Запуск на устройстве
— у тебя локально.

## Что в рамках / вне рамок
**В рамках Фазы 7:**
- Слои `data → domain → presentation` (минимальный clean-стиль на Riverpod).
- API-клиент (Dio + интерсептор JWT), безопасное хранение токена
  (`flutter_secure_storage`).
- Маршрутизация на `go_router` (декларативная, удобно для guard-ов и deep-links).
- Экраны: SplashGate, Login, Register, Profile, MenuList, MenuDetail,
  GenerateMenu, Prices, Cart.
- Запуск дип-линков из корзины через `url_launcher`.
- Виджет-тесты ключевых экранов (с моком репозитория).
- Конфиг базового URL API через `--dart-define=API_BASE_URL=...` (default
  `http://localhost:8000`).

**Вне рамок:**
- Дизайн-система/полноценная вёрстка под бренд (Material 3 дефолт, минимальные стили).
- Google OAuth на клиенте (бэк уже принимает ID-токен; нужен `google_sign_in`
  и SHA-конфиг — отдельной мини-фазой).
- Push-уведомления, offline-режим.
- Боевые адаптеры провайдеров доставки на бэке.

## Структура `apps/mobile/lib`
```
lib/
├── main.dart                   ProviderScope + MaterialApp.router
├── app/
│   ├── router.dart             go_router + guards (auth)
│   └── theme.dart              Material 3, простой ColorScheme
├── core/
│   ├── env.dart                API_BASE_URL из --dart-define
│   ├── api_client.dart         Dio + interceptor (Bearer, 401→logout)
│   ├── secure_storage.dart     обёртка над flutter_secure_storage
│   └── result.dart             Result/Failure для UI-обработки ошибок
├── features/
│   ├── auth/
│   │   ├── data/auth_repository.dart
│   │   ├── application/auth_controller.dart   (Notifier, AuthState)
│   │   └── presentation/{login_page.dart, register_page.dart, splash_gate.dart}
│   ├── profile/
│   │   ├── data/profile_repository.dart
│   │   ├── domain/profile.dart                (модель)
│   │   ├── application/profile_controller.dart
│   │   └── presentation/profile_page.dart
│   ├── menu/
│   │   ├── data/menu_repository.dart
│   │   ├── domain/menu.dart
│   │   ├── application/{menu_list_controller.dart, menu_detail_controller.dart, generate_menu_controller.dart}
│   │   └── presentation/{menu_list_page.dart, menu_detail_page.dart, generate_menu_page.dart}
│   ├── pricing/
│   │   ├── data/pricing_repository.dart
│   │   ├── domain/price_quote.dart
│   │   ├── application/pricing_controller.dart
│   │   └── presentation/prices_page.dart
│   └── cart/
│       ├── data/cart_repository.dart
│       ├── domain/cart.dart
│       ├── application/cart_controller.dart
│       └── presentation/cart_page.dart
└── shared/widgets/             общие виджеты (FormFields, LoadingButton, ErrorView)
```

## Маршруты (go_router)
- `/splash` — проверяет токен (есть/нет, валиден ли через `/auth/me`).
- `/login`, `/register`
- `/profile` (главный экран после логина — заполнение целей/аллергий)
- `/menu` — список меню
- `/menu/generate` — форма генерации (days_count, include_snacks, note)
- `/menu/:id` — детали меню (дни/приёмы пищи/КБЖУ/ингредиенты)
- `/menu/:id/prices` — сравнение по провайдерам
- `/menu/:id/cart` — корзина (per-item ссылки, кнопка «Открыть»)

Guard: если нет токена → `/login`; если на `/login`/`/register` с токеном → `/menu`.

## Зависимости (`apps/mobile/pubspec.yaml`)
```
flutter_riverpod: ^2.5
go_router:       ^14
dio:             ^5.5
flutter_secure_storage: ^9
url_launcher:    ^6
freezed_annotation: ^2.4  (для domain-моделей; freezed/json_serializable в dev)
json_annotation: ^4.9
intl:            ^0.19
```
dev: `build_runner`, `freezed`, `json_serializable`, `mocktail`, `flutter_lints` (есть).

## Состояние и ошибки
- `Riverpod` `AsyncNotifier`/`Notifier` для каждого фичевого контроллера.
- 401 от API → `AuthController.logout()`, маршрут → `/login`.
- Универсальная `ErrorView` с retry; `LoadingButton` с прогрессом.

## Тесты (CI)
- Виджет-тесты: рендер `LoginPage` (валидация формы), `ProfilePage` (загрузка/сохранение),
  `MenuListPage` (пустой/с данными), `MenuDetailPage` (отображение КБЖУ), `PricesPage`
  (сортировка/«самый дешёвый»), `CartPage` (нажатие на ссылку вызывает launcher).
- Репозитории мокаются через `mocktail`; `dio` не зовётся реально.
- CI уже запускает `flutter analyze` + `flutter test`.

## Конфиг
- `--dart-define=API_BASE_URL=http://10.0.2.2:8000` для Android-эмулятора;
  default для web/desktop — `http://localhost:8000`.
- Документируем в README команды запуска.

## Открытые вопросы (нужно подтверждение)
1. **Объём PR**: всё в одном PR (рекоменд., каркас + все экраны минимально) или
   разбить на под-фазы (auth → profile → menu → pricing → cart)?
2. **HTTP-клиент**: `dio` (рекоменд., интерсепторы/ретраи) или `package:http`?
3. **Навигация**: `go_router` (рекоменд., декларативная, deep-links) или Navigator 1.0?
4. **Хранение токена**: `flutter_secure_storage` (рекоменд., keychain/keystore)
   или `shared_preferences`?
5. **Google Sign-In на клиенте**: вне Фазы 7 (рекоменд., требует SHA/конфигов
   платформ) — отдельной мини-фазой позже?
6. **Базовый URL API**: `--dart-define=API_BASE_URL=...` (рекоменд.) или хардкод
   с тремя профилями?

После подтверждения реализую одним PR: pubspec, каркас (router/theme/api/secure storage),
все экраны и виджет-тесты; прогоню `flutter analyze`/`flutter test` локально не смогу,
полная проверка — в CI.
