BEGIN;

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    login           VARCHAR(64)  NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT users_login_not_blank CHECK (char_length(trim(login)) > 0),
    CONSTRAINT users_first_name_not_blank CHECK (char_length(trim(first_name)) > 0),
    CONSTRAINT users_last_name_not_blank CHECK (char_length(trim(last_name)) > 0)
);

CREATE UNIQUE INDEX idx_users_login_lower ON users (lower(login));
CREATE INDEX idx_users_full_name_trgm
    ON users USING gin ((first_name || ' ' || last_name) gin_trgm_ops);

CREATE TABLE drivers (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER     NOT NULL,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT drivers_user_id_unique UNIQUE (user_id),
    CONSTRAINT fk_drivers_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_drivers_user_id ON drivers (user_id);

CREATE TABLE trips (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER     NOT NULL,
    driver_id       INTEGER,
    status          VARCHAR(20) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_trips_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_trips_driver FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE SET NULL,
    CONSTRAINT trips_status_check CHECK (status IN ('pending', 'active', 'completed'))
);

CREATE INDEX idx_trips_user_id ON trips (user_id);
CREATE INDEX idx_trips_driver_id ON trips (driver_id) WHERE driver_id IS NOT NULL;
CREATE INDEX idx_trips_status_created ON trips (status, created_at DESC);
CREATE INDEX idx_trips_user_status_created ON trips (user_id, status, created_at DESC);

COMMIT;
