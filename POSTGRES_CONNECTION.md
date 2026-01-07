# Connecting to PostgreSQL via Terminal

## Quick Connection

Since you installed PostgreSQL 15 via Homebrew, you can connect using:

```bash
# Option 1: Connect to default database (postgres)
psql postgres

# Option 2: Connect directly to your deckd database
psql deckd

# Option 3: Full connection string (if you need to specify user/host)
psql -U your_username -d deckd -h localhost
```

## If `psql` Command Not Found

Since PostgreSQL 15 is keg-only, you may need to use the full path or add it to your PATH:

```bash
# Use full path
/opt/homebrew/opt/postgresql@15/bin/psql postgres

# Or add to PATH (add this to your ~/.zshrc)
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
```

After adding to PATH, reload your shell:
```bash
source ~/.zshrc
```

## Finding Your Database Connection Details

Your database details are in your `.env` file. Check it:

```bash
cd backend
cat .env | grep DATABASE_URL
```

The format is usually:
```
postgresql://username:password@localhost:5432/database_name
```

## Common Connection Commands

### Connect as specific user
```bash
psql -U your_username -d deckd
```

### Connect with password prompt
```bash
psql -U your_username -d deckd -W
```

### Connect to specific host and port
```bash
psql -h localhost -p 5432 -U your_username -d deckd
```

## Once Connected - Useful Commands

### List all databases
```sql
\l
-- or
\list
```

### Connect to a different database
```sql
\c deckd
```

### List all tables
```sql
\dt
```

### Describe a table structure
```sql
\d users
\d dj_sets
```

### List all schemas
```sql
\dn
```

### Show current database
```sql
SELECT current_database();
```

### Show current user
```sql
SELECT current_user;
```

### View table data
```sql
SELECT * FROM users;
SELECT * FROM dj_sets LIMIT 10;
```

### Count records
```sql
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM dj_sets;
```

### Exit psql
```sql
\q
-- or just
exit
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `\l` | List databases |
| `\c dbname` | Connect to database |
| `\dt` | List tables |
| `\d tablename` | Describe table |
| `\du` | List users/roles |
| `\q` | Quit/exit |
| `\?` | Help |
| `\h` | SQL help |

## Example Session

```bash
# Connect to database
$ psql deckd

# Once connected:
deckd=# \dt
                    List of relations
 Schema |            Name             | Type  | Owner
--------+-----------------------------+-------+-------
 public | alembic_version             | table | nathanrancie
 public | dj_sets                     | table | nathanrancie
 public | follows                     | table | nathanrancie
 public | list_items                  | table | nathanrancie
 public | lists                       | table | nathanrancie
 public | ratings                     | table | nathanrancie
 public | reviews                     | table | nathanrancie
 public | user_set_logs               | table | nathanrancie
 public | users                       | table | nathanrancie

deckd=# SELECT COUNT(*) FROM users;
 count
-------
     1

deckd=# SELECT username, email FROM users;
 username |        email
----------+--------------------
 Rancie   | nathrancie@gmail.com

deckd=# \q
```

## Troubleshooting

### "psql: error: connection to server failed"
- Make sure PostgreSQL is running: `brew services list`
- Start it: `brew services start postgresql@15`

### "database does not exist"
- Create it: `createdb deckd`
- Or connect to default: `psql postgres` then `CREATE DATABASE deckd;`

### "password authentication failed"
- Check your `.env` file for the correct password
- Or connect without password if using peer authentication (default on macOS)

### "role does not exist"
- Your macOS username should work by default
- Or create a user: `CREATE USER your_username WITH PASSWORD 'password';`

## Creating the Database (if needed)

If the database doesn't exist yet:

```bash
# Connect to default postgres database
psql postgres

# Create the database
CREATE DATABASE deckd;

# Exit
\q
```

## Setting Up User Permissions (if needed)

```sql
-- Connect as superuser
psql postgres

-- Create user (if needed)
CREATE USER your_username WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE deckd TO your_username;

-- Connect to deckd database
\c deckd

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO your_username;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
```

