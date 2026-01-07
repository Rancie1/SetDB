# How to Delete a DJ Set

There are several ways to delete a DJ set you've imported:

## Method 1: Using PostgreSQL Terminal (Quickest)

### Step 1: Connect to your database
```bash
psql deckd
# Or if psql not in PATH:
/opt/homebrew/opt/postgresql@15/bin/psql deckd
```

### Step 2: Find the set you want to delete
```sql
-- List all sets with their IDs
SELECT id, title, dj_name, source_type, created_at 
FROM dj_sets 
ORDER BY created_at DESC;
```

### Step 3: Delete the set
```sql
-- Replace 'set-id-here' with the actual UUID from step 2
DELETE FROM dj_sets WHERE id = 'set-id-here';
```

**Example:**
```sql
deckd=# SELECT id, title, dj_name FROM dj_sets;
                  id                  |           title            |  dj_name
--------------------------------------+---------------------------+------------
 123e4567-e89b-12d3-a456-426614174000 | Example DJ Set            | DJ Name
 987fcdeb-51a2-43f1-b123-456789abcdef | Another Set              | Another DJ

deckd=# DELETE FROM dj_sets WHERE id = '123e4567-e89b-12d3-a456-426614174000';
DELETE 1

deckd=# \q
```

### Delete by title (if you know it)
```sql
DELETE FROM dj_sets WHERE title = 'Set Title Here';
```

### Delete all sets from a specific source
```sql
-- Delete all YouTube sets
DELETE FROM dj_sets WHERE source_type = 'youtube';

-- Delete all SoundCloud sets
DELETE FROM dj_sets WHERE source_type = 'soundcloud';
```

## Method 2: Using the API Endpoint

You can use the DELETE endpoint if you know the set ID:

```bash
# Replace SET_ID with the actual UUID
# Replace YOUR_TOKEN with your JWT token
curl -X DELETE \
  http://localhost:8000/api/sets/SET_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Note:** You can only delete sets you created (the API checks this).

## Method 3: Using a Frontend UI (Coming Soon)

We can add a delete button to the set cards in the frontend. Would you like me to add that?

## Important Notes

⚠️ **Cascade Deletes**: When you delete a set, you might want to also delete related data:

```sql
-- Check what's related to the set
SELECT * FROM user_set_logs WHERE set_id = 'set-id-here';
SELECT * FROM reviews WHERE set_id = 'set-id-here';
SELECT * FROM ratings WHERE set_id = 'set-id-here';
SELECT * FROM list_items WHERE set_id = 'set-id-here';

-- Delete related data first (if needed)
DELETE FROM list_items WHERE set_id = 'set-id-here';
DELETE FROM ratings WHERE set_id = 'set-id-here';
DELETE FROM reviews WHERE set_id = 'set-id-here';
DELETE FROM user_set_logs WHERE set_id = 'set-id-here';

-- Then delete the set
DELETE FROM dj_sets WHERE id = 'set-id-here';
```

**Or delete everything in one go** (if you're sure):
```sql
-- This will fail if there are foreign key constraints
-- You may need to delete related records first
DELETE FROM dj_sets WHERE id = 'set-id-here';
```

## Quick Reference

### Find sets by title
```sql
SELECT id, title, dj_name FROM dj_sets 
WHERE title ILIKE '%search term%';
```

### Find sets by DJ name
```sql
SELECT id, title, dj_name FROM dj_sets 
WHERE dj_name ILIKE '%dj name%';
```

### Find your sets (if you know your user ID)
```sql
SELECT id, title, dj_name FROM dj_sets 
WHERE created_by_id = 'your-user-id-here';
```

### Count sets before/after deletion
```sql
SELECT COUNT(*) FROM dj_sets;
```

