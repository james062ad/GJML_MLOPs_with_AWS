/* Create the vector extension */
CREATE EXTENSION IF NOT EXISTS vector;

/*
 * Vector dimension explanation:
 * The dimension 384 is commonly used with models like:
 * - all-MiniLM-L6-v2 (384 dimensions)
 * - all-mpnet-base-v2 (384 dimensions)
 * 
 * Different models have different embedding dimensions:
 * - BERT base: 768 dimensions
 * - BERT large: 1024 dimensions
 * - OpenAI text-embedding-ada-002: 1536 dimensions
 * - OpenAI text-embedding-3-small: 1536 dimensions
 * - OpenAI text-embedding-3-large: 3072 dimensions
 * 
 * If using a different model, adjust the vector dimension accordingly.
 * For example, if using OpenAI's text-embedding-ada-002, change to:
 * embedding vector(1536)
 */
CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    chunk TEXT NOT NULL,
    embedding vector(384)
);