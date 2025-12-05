-- Таблица для хранения чанков документов с embeddings (для RAG)
CREATE TABLE IF NOT EXISTS public.chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(doc_id, chunk_index)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON public.chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON public.chunks USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON public.chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Функция для поиска похожих документов (match_documents)
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_count int DEFAULT 6,
    filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id uuid,
    doc_id text,
    chunk_index integer,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.doc_id,
        c.chunk_index,
        c.content,
        c.metadata,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM public.chunks c
    WHERE 
        -- Фильтр по source_type если указан
        (filter->>'source_type' IS NULL OR c.metadata->>'source_type' = filter->>'source_type')
        -- Фильтр по doc_id если указан
        AND (filter->>'doc_id' IS NULL OR c.doc_id = filter->>'doc_id')
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- RLS политики для chunks (публичный доступ для чтения)
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to chunks" ON public.chunks
    FOR SELECT
    USING (true);

CREATE POLICY "Allow service role full access to chunks" ON public.chunks
    FOR ALL
    USING (auth.role() = 'service_role');

