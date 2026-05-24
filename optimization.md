# Оптимизация запросов

Замеры на PostgreSQL 16, данные из `data.sql`. Перед `EXPLAIN`:

```bash
docker compose up -d taxi-postgres
docker compose exec taxi-postgres psql -U user -d taxidb -c "ANALYZE users; ANALYZE drivers; ANALYZE trips;"
```

На наших ~17 пользователях и 12 поездках planner чаще берёт **Seq Scan** — таблица настолько мала, что индекс дороже. Ниже сначала реальный план «как есть», потом сравнение индексов с `SET enable_seqscan = off` (чтобы увидеть, какой индекс выберется на большем объёме).

## Поиск по логину

`GET /users/by-login/{login}`

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, login, first_name, last_name, password_hash
FROM users WHERE lower(login) = lower('ivan_p');
```

**Фактический план:**

```
 Seq Scan on users  (cost=0.00..1.25 rows=1 width=46) (actual time=0.007..0.011 rows=1 loops=1)
   Filter: (lower((login)::text) = 'ivan_p'::text)
   Rows Removed by Filter: 16
   Buffers: shared hit=1
 Planning Time: 0.513 ms
 Execution Time: 0.040 ms
```

С `enable_seqscan = off` — используется `idx_users_login_lower`:

```
 Index Scan using idx_users_login_lower on users  (cost=0.14..8.15 rows=1 width=46) (actual time=0.038..0.038 rows=1 loops=1)
   Index Cond: (lower((login)::text) = 'ivan_p'::text)
 Execution Time: 0.061 ms
```

## Поиск по ФИО

`GET /users/search`

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, login, first_name, last_name, password_hash
FROM users
WHERE (first_name || ' ' || last_name) ILIKE '%Иван%'
ORDER BY last_name, first_name;
```

**Фактический план:**

```
 Sort  (cost=1.31..1.31 rows=1 width=46) (actual time=0.041..0.041 rows=1 loops=1)
   Sort Key: last_name, first_name
   ->  Seq Scan on users  (cost=0.00..1.30 rows=1 width=46) (actual time=0.006..0.016 rows=1 loops=1)
         Filter: ((((first_name)::text || ' '::text) || (last_name)::text) ~~* '%Иван%'::text)
 Execution Time: 0.053 ms
```

GIN `idx_users_full_name_trgm` на тысячах строк обычно даёт Bitmap Index Scan; у нас planner правомерно сканирует всю таблицу.

## Активные заказы

`GET /trips/active`

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, user_id, driver_id, status, created_at
FROM trips
WHERE status IN ('pending', 'active')
ORDER BY created_at DESC;
```

**Без принуждения — Seq Scan + Sort:**

```
 Sort  (cost=1.21..1.22 rows=5 width=29) (actual time=0.010..0.010 rows=5 loops=1)
   Sort Key: created_at DESC
   ->  Seq Scan on trips  (cost=0.00..1.15 rows=5 width=29) (actual time=0.004..0.005 rows=5 loops=1)
         Filter: ((status)::text = ANY ('{pending,active}'::text[]))
 Execution Time: 0.018 ms
```

**С `enable_seqscan = off` — `idx_trips_status_created`:**

```
 Sort  (cost=12.42..12.44 rows=5 width=28) (actual time=0.277..0.278 rows=5 loops=1)
   ->  Index Scan using idx_trips_status_created on trips  (cost=0.14..12.37 rows=5 width=28)
         Index Cond: ((status)::text = ANY ('{pending,active}'::text[]))
 Execution Time: 0.316 ms
```

Отдельный индекс только по `status` не делал: для этого запроса хватает составного `(status, created_at DESC)`. Отдельный `created_at` тоже убрал — он дублировал бы сортировку внутри `status_created`.

## История поездок

`GET /users/{user_id}/trips/history`

Сравнение: составной индекс vs только `idx_trips_user_id`. Замеры с `enable_seqscan = off`.

**С `idx_trips_user_status_created`:**

```
 Index Scan using idx_trips_user_status_created on trips  (cost=0.14..8.17 rows=2 width=28) (actual time=0.020..0.021 rows=2 loops=1)
   Index Cond: ((user_id = 1) AND ((status)::text = 'completed'::text))
 Execution Time: 0.031 ms
```

**После `DROP INDEX idx_trips_user_status_created` — только `idx_trips_user_id`:**

```
 Sort  (cost=8.21..8.21 rows=2 width=28) (actual time=0.037..0.037 rows=2 loops=1)
   Sort Key: created_at DESC
   ->  Index Scan using idx_trips_user_id on trips  (cost=0.14..8.20 rows=2 width=28) (actual time=0.025..0.026 rows=2 loops=1)
         Index Cond: (user_id = 1)
         Filter: ((status)::text = 'completed'::text)
         Rows Removed by Filter: 1
 Execution Time: 0.051 ms
```

Разница: фильтр по `status` и сортировка по `created_at` уходят в отдельные шаги. На большой истории это заметнее.

## Принять заказ

`POST /trips/{id}/accept`

```sql
EXPLAIN (ANALYZE, BUFFERS)
UPDATE trips SET driver_id = 3, status = 'active'
WHERE id = 8 AND status = 'pending'
RETURNING id, user_id, driver_id, status, created_at;
```

**Фактический план:**

```
 Update on trips  (cost=0.00..1.18 rows=1 width=68) (actual time=0.811..0.812 rows=1 loops=1)
   ->  Seq Scan on trips  (cost=0.00..1.18 rows=1 width=68) (actual time=0.011..0.012 rows=1 loops=1)
         Filter: ((id = 8) AND ((status)::text = 'pending'::text))
 Execution Time: 1.932 ms
```

По `id` на малых данных снова seq scan; на проде сработает PK.

## Индексы в schema.sql

- `idx_users_login_lower` — логин без учёта регистра
- `idx_users_full_name_trgm` — ILIKE по ФИО
- `idx_trips_user_id` — FK, отчёты по клиенту
- `idx_trips_driver_id` — FK (partial, только назначенные)
- `idx_trips_status_created` — активные заказы
- `idx_trips_user_status_created` — история

## Партиционирование

Если `trips` вырастет — RANGE по `created_at` (месяц). Запросы с диапазоном дат не лезут в старые партиции.
