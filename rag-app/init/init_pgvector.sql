
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS papers;

CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    chunk TEXT NOT NULL,
    embedding vector(1024)
);
