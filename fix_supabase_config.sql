-- SQL script to fix common Supabase configuration issues for Project Aegis

-- 1. Enable replication for realtime functionality
ALTER TABLE verified_claims REPLICA IDENTITY FULL;
ALTER TABLE system_logs REPLICA IDENTITY FULL;

-- 2. Enable Row Level Security (RLS)
ALTER TABLE verified_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- 3. Create policies for public read access
CREATE POLICY "public_read_verified_claims" ON verified_claims FOR SELECT USING (true);
CREATE POLICY "public_read_system_logs" ON system_logs FOR SELECT USING (true);

-- 4. Grant access to anon role
GRANT SELECT ON verified_claims TO anon;
GRANT SELECT ON system_logs TO anon;

-- 5. Check existing publications
SELECT * FROM supabase_realtime.publications;

-- 6. Add tables to realtime publication (run this if tables are not in publication)
BEGIN;
DROP PUBLICATION IF EXISTS supabase_realtime;
CREATE PUBLICATION supabase_realtime FOR TABLE verified_claims, system_logs;
COMMIT;

-- 7. Verify the configuration
SELECT 
    tablename,
    schemaname,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE tablename IN ('verified_claims', 'system_logs');

-- 8. Check RLS status
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    forcerowsecurity
FROM pg_tables 
WHERE tablename IN ('verified_claims', 'system_logs');

-- 9. Check policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies 
WHERE tablename IN ('verified_claims', 'system_logs');