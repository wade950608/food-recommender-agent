CREATE TABLE IF NOT EXISTS decisions (
    id         SERIAL PRIMARY KEY,
    prompt     TEXT NOT NULL,
    result     JSONB NOT NULL,
    model      TEXT NOT NULL,
    latency_ms INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
