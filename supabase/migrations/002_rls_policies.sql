-- Row Level Security Policies

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faq_kb ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_logs ENABLE ROW LEVEL SECURITY;

-- Users policies
-- Политика 1: Пользователь может видеть свой профиль
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Политика 2: Все авторизованные пользователи могут видеть всех пользователей
-- (Исправлено: убрана рекурсия - больше не проверяем роль через users внутри политики)
CREATE POLICY "Authenticated users can view all users"
    ON public.users FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Departments policies
CREATE POLICY "Everyone can view departments"
    ON public.departments FOR SELECT
    USING (true);

CREATE POLICY "Admins can manage departments"
    ON public.departments FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Clients policies
CREATE POLICY "Users can view clients"
    ON public.clients FOR SELECT
    USING (true);

CREATE POLICY "Admins and operators can manage clients"
    ON public.clients FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role IN ('admin', 'operator', 'call_agent')
        )
    );

-- Tickets policies
CREATE POLICY "Users can view tickets in their department"
    ON public.tickets FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.users u
            WHERE u.id = auth.uid()
            AND (
                u.role = 'admin'
                OR u.role = 'supervisor'
                OR (u.role = 'department_user' AND u.department_id = tickets.department_id)
                OR tickets.assigned_to = auth.uid()
                OR tickets.engineer_id = auth.uid()
            )
        )
    );

CREATE POLICY "Call agents can create tickets"
    ON public.tickets FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role IN ('call_agent', 'admin', 'operator')
        )
    );

CREATE POLICY "Department users can update tickets in their department"
    ON public.tickets FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.users u
            WHERE u.id = auth.uid()
            AND (
                u.role = 'admin'
                OR (u.role = 'department_user' AND u.department_id = tickets.department_id)
                OR tickets.assigned_to = auth.uid()
            )
        )
    );

-- Messages policies
CREATE POLICY "Users can view messages for tickets they can access"
    ON public.messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.tickets t
            JOIN public.users u ON u.id = auth.uid()
            WHERE t.id = messages.ticket_id
            AND (
                u.role = 'admin'
                OR u.role = 'supervisor'
                OR (u.role = 'department_user' AND u.department_id = t.department_id)
                OR t.assigned_to = auth.uid()
            )
        )
    );

CREATE POLICY "Users can create messages for tickets they can access"
    ON public.messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.tickets t
            JOIN public.users u ON u.id = auth.uid()
            WHERE t.id = messages.ticket_id
            AND (
                u.role = 'admin'
                OR (u.role = 'department_user' AND u.department_id = t.department_id)
                OR t.assigned_to = auth.uid()
            )
        )
    );

-- FAQ KB policies
CREATE POLICY "Everyone can view FAQ"
    ON public.faq_kb FOR SELECT
    USING (true);

CREATE POLICY "Admins can manage FAQ"
    ON public.faq_kb FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- AI Logs policies
CREATE POLICY "Admins and supervisors can view AI logs"
    ON public.ai_logs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role IN ('admin', 'supervisor')
        )
    );

