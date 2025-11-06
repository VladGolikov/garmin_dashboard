CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    garmin_activity_id BIGINT UNIQUE NOT NULL,
    start_time_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    distance_km NUMERIC(10, 3) NOT NULL CHECK (distance_km > 0)
);

-- Индекс для быстрых агрегаций по времени
CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities (start_time_utc);