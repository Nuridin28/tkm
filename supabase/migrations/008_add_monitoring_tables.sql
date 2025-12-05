-- Таблица для отслеживания классификации и обратной связи
CREATE TABLE IF NOT EXISTS public.classification_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    predicted_category TEXT,
    predicted_department TEXT,
    predicted_priority TEXT,
    actual_category TEXT,
    actual_department TEXT,
    actual_priority TEXT,
    confidence_score FLOAT,
    feedback_by UUID REFERENCES public.users(id),
    feedback_at TIMESTAMPTZ DEFAULT NOW(),
    is_correct BOOLEAN,
    notes TEXT
);

-- Таблица для отслеживания времени ответа
CREATE TABLE IF NOT EXISTS public.response_times (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    first_response_at TIMESTAMPTZ,
    response_time_seconds INTEGER,
    responder_id UUID REFERENCES public.users(id),
    response_type TEXT CHECK (response_type IN ('ai', 'human', 'auto'))
);

-- Таблица для отслеживания ошибок маршрутизации
CREATE TABLE IF NOT EXISTS public.routing_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
    initial_department_id UUID REFERENCES public.departments(id),
    correct_department_id UUID REFERENCES public.departments(id),
    routed_at TIMESTAMPTZ DEFAULT NOW(),
    routed_by UUID REFERENCES public.users(id),
    error_type TEXT CHECK (error_type IN ('wrong_department', 'wrong_priority', 'should_auto_resolve'))
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_classification_feedback_ticket ON public.classification_feedback(ticket_id);
CREATE INDEX IF NOT EXISTS idx_classification_feedback_date ON public.classification_feedback(feedback_at);
CREATE INDEX IF NOT EXISTS idx_response_times_ticket ON public.response_times(ticket_id);
CREATE INDEX IF NOT EXISTS idx_routing_errors_ticket ON public.routing_errors(ticket_id);
CREATE INDEX IF NOT EXISTS idx_routing_errors_date ON public.routing_errors(routed_at);

-- Добавляем поля в tickets для отслеживания времени ответа
ALTER TABLE public.tickets 
ADD COLUMN IF NOT EXISTS first_response_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS classification_confidence FLOAT,
ADD COLUMN IF NOT EXISTS ai_processing_time_ms INTEGER;

