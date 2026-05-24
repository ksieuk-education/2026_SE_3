# Домашнее задание №3 — PostgreSQL

Учебный сервис заказа поездок: пользователи, водители, поездки. API из прошлой лабы (FastAPI + asyncpg), БД — PostgreSQL в Docker.

Скрипты: `schema.sql`, `data.sql`, `queries.sql`, разбор планов — `optimization.md`.

## Схема

Три таблицы: `users` (логин, ФИО, пароль), `drivers` (один user — один водитель), `trips` (клиент, опционально водитель, статус `pending` → `active` → `completed`).

Отдельные индексы по `trips.status` и `trips.created_at` не заводил: для `/trips/active` хватает составного `(status, created_at DESC)`, для истории — `(user_id, status, created_at DESC)`.

## Запуск

```bash
cp .env.example .env
cp .configs/config.yaml.example .configs/config.yaml
docker compose up -d --build
```

Postgres: `localhost:5432` (user / taxipass / taxidb). API: http://localhost:8000/api/taxi/v1/docs

При первом старте postgres сам накатывает `schema.sql` и `data.sql`. Вручную: `psql -h localhost -U user -d taxidb -f schema.sql` и `-f data.sql`.

## Что проверял

Поднял `docker compose up -d --build` — postgres healthy, API отвечает.

```bash
curl http://localhost:8000/api/taxi/v1/health
# {"status":"healthy",...}

curl http://localhost:8000/api/taxi/v1/users/by-login/ivan_p
# нашёл Ивана Петрова

curl "http://localhost:8000/api/taxi/v1/users/search?name_mask=Иван"
# один результат

curl http://localhost:8000/api/taxi/v1/trips/active
# pending/active, в т.ч. заказ id=8 с января (зависший pending)
```

Логин `test_auth` / пароль `secret123` — для `/auth/login`. Водители: `volkov_a`, `orlov_d`, `morozov_s` и остальные с `user_id` 2, 5, 7–14.

В `data.sql` специально кривые кейсы: поездка #12 `completed` с датой 2025-11-30, #8 `pending` с 2026-01-03 — чтобы в отчётах было видно «старые» заказы.

`EXPLAIN` гонял через `docker compose exec taxi-postgres psql ...` — выводы в `optimization.md`. На малых таблицах planner честно выбирает Seq Scan; для сравнения индексов там же есть прогон с `enable_seqscan = off`.

## API

Префикс `/api/taxi/v1` — пользователи, водители, поездки, auth. SQL в `queries.sql`.
