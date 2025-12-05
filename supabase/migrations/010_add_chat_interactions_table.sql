-- Таблица для отслеживания всех взаимодействий с ИИ ассистентом в публичном чате
-- Это нужно для правильного подсчета авторешений и SLA соответствия
-- 
-- АВТОРЕШЕНИЕ = когда ticket_created = FALSE (ИИ ответил без создания тикета)
-- SLA = время ответа ИИ ассистента (response_time_ms)

CREATE TABLE IF NOT EXISTS public.chat_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT,  -- ID пользователя (phone или anonymous)
    client_type TEXT CHECK (client_type IN ('corporate', 'private')),
    message TEXT NOT NULL,  -- Запрос пользователя
    ai_response TEXT NOT NULL,  -- Ответ ИИ ассистента
    conversation_history JSONB DEFAULT '[]',  -- История разговора до этого сообщения
    ticket_created BOOLEAN DEFAULT FALSE,  -- Был ли создан тикет (FALSE = авторешение)
    ticket_id UUID REFERENCES public.tickets(id) ON DELETE SET NULL,  -- ID созданного тикета (если был создан)
    confidence FLOAT,  -- Уверенность ИИ в ответе (0.0-1.0)
    max_similarity FLOAT,  -- Максимальная релевантность найденных чанков
    is_technical_issue BOOLEAN DEFAULT FALSE,  -- Была ли это техническая проблема
    ai_explicitly_requested_ticket BOOLEAN DEFAULT FALSE,  -- Явно ли AI запросил тикет
    category TEXT,  -- Категория (если тикет был создан)
    subcategory TEXT,  -- Подкатегория
    department TEXT,  -- Департамент
    priority TEXT,  -- Приоритет
    language TEXT DEFAULT 'ru',  -- Язык
    response_time_ms INTEGER,  -- Время ответа ИИ в миллисекундах (для SLA)
    sources JSONB DEFAULT '[]',  -- Источники из RAG (chunks) с метаданными
    session_id TEXT,  -- ID сессии чата (для группировки взаимодействий одного пользователя)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_chat_interactions_user ON public.chat_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_interactions_created ON public.chat_interactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_interactions_ticket_created ON public.chat_interactions(ticket_created);
CREATE INDEX IF NOT EXISTS idx_chat_interactions_ticket_id ON public.chat_interactions(ticket_id);
CREATE INDEX IF NOT EXISTS idx_chat_interactions_session ON public.chat_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_interactions_auto_resolve ON public.chat_interactions(ticket_created, created_at) WHERE ticket_created = FALSE;

-- RLS политики
ALTER TABLE public.chat_interactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access to chat_interactions" ON public.chat_interactions
    FOR ALL
    USING (auth.role() = 'service_role');

-- Комментарии для документации
COMMENT ON TABLE public.chat_interactions IS 'Отслеживание всех взаимодействий с ИИ ассистентом в публичном чате для подсчета метрик авторешений и SLA';
COMMENT ON COLUMN public.chat_interactions.ticket_created IS 'TRUE если был создан тикет, FALSE если ИИ ответил без создания тикета (это и есть АВТОРЕШЕНИЕ)';
COMMENT ON COLUMN public.chat_interactions.response_time_ms IS 'Время ответа ИИ ассистента в миллисекундах (для расчета SLA соответствия)';
COMMENT ON COLUMN public.chat_interactions.session_id IS 'ID сессии чата для группировки взаимодействий одного пользователя';

