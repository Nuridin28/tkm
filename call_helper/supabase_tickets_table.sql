-- Create tickets table for Help Desk system
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.tickets (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  client_type TEXT NOT NULL CHECK (client_type IN ('corporate', 'private')),
  language TEXT NOT NULL DEFAULT 'ru' CHECK (language IN ('ru', 'kz', 'en')),
  category TEXT NOT NULL CHECK (category IN ('network', 'telephony', 'tv', 'billing', 'equipment', 'other')),
  subcategory TEXT,
  department TEXT NOT NULL CHECK (department IN ('TechSupport', 'Network', 'Sales', 'Billing', 'LocalOffice')),
  priority TEXT NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  auto_resolve_candidate BOOLEAN NOT NULL DEFAULT false,
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
  content TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  assigned_to TEXT,
  resolution_notes TEXT
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON public.tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON public.tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON public.tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON public.tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON public.tickets(priority);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_tickets_updated_at 
    BEFORE UPDATE ON public.tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
ALTER TABLE public.tickets ENABLE ROW LEVEL SECURITY;

-- Policy to allow service role to insert tickets
CREATE POLICY "Service role can insert tickets"
    ON public.tickets
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Policy to allow service role to read tickets
CREATE POLICY "Service role can read tickets"
    ON public.tickets
    FOR SELECT
    TO service_role
    USING (true);

-- Policy to allow service role to update tickets
CREATE POLICY "Service role can update tickets"
    ON public.tickets
    FOR UPDATE
    TO service_role
    USING (true);

