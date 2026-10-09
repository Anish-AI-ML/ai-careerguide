-- Run once in the Supabase SQL editor after the tables exist.
-- This API talks to Postgres directly (as the postgres role, which bypasses row level security), so the
-- Supabase auto-generated REST API should have no access to these tables. Enabling RLS with no policies
-- denies the anon and authenticated roles everything.
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
  END LOOP;
END $$;
