-- Cleanup script: Remove events from dj_sets table that exist in events table
-- These rows were copied to the events table but not deleted from dj_sets during migration

-- First, check what will be deleted
SELECT ds.id, ds.title, ds.dj_name 
FROM dj_sets ds
INNER JOIN events e ON ds.id = e.id;

-- Then delete them
DELETE FROM dj_sets
WHERE id IN (SELECT id FROM events);

-- Verify they're gone
SELECT COUNT(*) as remaining_event_sets 
FROM dj_sets ds
INNER JOIN events e ON ds.id = e.id;
-- Should return 0
