-- POST /users
INSERT INTO users (login, first_name, last_name, password_hash)
VALUES (:login, :first_name, :last_name, '')
RETURNING id, login, first_name, last_name, password_hash;

-- POST /auth/register
INSERT INTO users (login, first_name, last_name, password_hash)
VALUES (:login, :first_name, :last_name, :password_hash)
RETURNING id, login, first_name, last_name, password_hash;

-- GET /users/by-login/{login}, POST /auth/login
SELECT id, login, first_name, last_name, password_hash
FROM users WHERE lower(login) = lower(:login);

-- GET /users/search
SELECT id, login, first_name, last_name, password_hash
FROM users
WHERE (first_name || ' ' || last_name) ILIKE :name_mask
ORDER BY last_name, first_name;

-- проверка user по id
SELECT id, login, first_name, last_name, password_hash
FROM users WHERE id = :user_id;

-- POST /drivers
INSERT INTO drivers (user_id) VALUES (:user_id)
RETURNING id, user_id;

-- POST /trips/{id}/accept — проверка водителя
SELECT id, user_id FROM drivers WHERE id = :driver_id;

-- POST /trips
INSERT INTO trips (user_id, driver_id, status)
VALUES (:user_id, NULL, 'pending')
RETURNING id, user_id, driver_id, status, created_at;

-- GET /trips/active
SELECT id, user_id, driver_id, status, created_at
FROM trips
WHERE status IN ('pending', 'active')
ORDER BY created_at DESC;

-- POST /trips/{trip_id}/accept
UPDATE trips
SET driver_id = :driver_id, status = 'active'
WHERE id = :trip_id AND status = 'pending'
RETURNING id, user_id, driver_id, status, created_at;

-- GET /users/{user_id}/trips/history
SELECT id, user_id, driver_id, status, created_at
FROM trips
WHERE user_id = :user_id AND status = 'completed'
ORDER BY created_at DESC;

-- POST /trips/{trip_id}/complete
UPDATE trips
SET status = 'completed'
WHERE id = :trip_id AND status = 'active'
RETURNING id, user_id, driver_id, status, created_at;

-- поездка по id
SELECT id, user_id, driver_id, status, created_at
FROM trips WHERE id = :trip_id;

-- отчёты
SELECT status, COUNT(*) AS cnt FROM trips GROUP BY status ORDER BY status;

SELECT d.id AS driver_id,
       u.first_name || ' ' || u.last_name AS driver_name,
       COUNT(t.id) FILTER (WHERE t.status = 'completed') AS completed_trips
FROM drivers d
JOIN users u ON u.id = d.user_id
LEFT JOIN trips t ON t.driver_id = d.id
GROUP BY d.id, u.first_name, u.last_name
ORDER BY completed_trips DESC;

SELECT t.id, t.status, t.created_at,
       cu.login AS client_login, du.login AS driver_login
FROM trips t
JOIN users cu ON cu.id = t.user_id
LEFT JOIN drivers d ON d.id = t.driver_id
LEFT JOIN users du ON du.id = d.user_id
WHERE t.status IN ('pending', 'active')
ORDER BY t.created_at DESC;
