-- Назначить департамент тикету
-- Тикет: c6977a47-761d-464d-987c-888b88e96c3b
-- Департамент: 378b7bf2-ae06-4bea-adc8-81b96dd36fe6

UPDATE public.tickets
SET 
    department_id = '378b7bf2-ae06-4bea-adc8-81b96dd36fe6',
    updated_at = NOW()
WHERE id = 'c6977a47-761d-464d-987c-888b88e96c3b';

-- Проверить результат
SELECT 
    t.id,
    t.subject,
    t.status,
    t.priority,
    d.name as department_name,
    d.id as department_id,
    t.updated_at
FROM public.tickets t
LEFT JOIN public.departments d ON t.department_id = d.id
WHERE t.id = 'c6977a47-761d-464d-987c-888b88e96c3b';

