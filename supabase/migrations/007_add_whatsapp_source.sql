-- Add whatsapp to ticket source enum
ALTER TABLE public.tickets
DROP CONSTRAINT IF EXISTS tickets_source_check;

ALTER TABLE public.tickets
ADD CONSTRAINT tickets_source_check 
CHECK (source IN ('portal', 'chat', 'email', 'phone', 'call_agent', 'telegram', 'whatsapp'));

