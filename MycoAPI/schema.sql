CREATE TABLE measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    time_of_measure TIMESTAMPTZ NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    humidity DOUBLE PRECISION NOT NULL CHECK (humidity BETWEEN 0 AND 100),
    within_tolerance BOOLEAN NOT NULL
);

CREATE INDEX measurements_time_idx
    ON measurements (time_of_measure DESC, id DESC);
