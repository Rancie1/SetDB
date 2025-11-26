# What is Alembic and Why Do We Need It?

## The Problem Alembic Solves

Imagine this scenario:
1. You develop your app with a `users` table
2. You deploy it to production
3. Later, you want to add a `phone_number` column to `users`
4. Your teammate also has the database locally
5. How do you:
   - Add the column to production?
   - Make sure your teammate's local database matches?
   - Keep track of all database changes?
   - Roll back if something goes wrong?

**Alembic solves this** by creating **database migrations** - version control for your database schema.

## What is a Migration?

A migration is a script that:
- **Upgrades** your database (adds tables, columns, indexes)
- **Downgrades** your database (removes them if needed)

Think of it like Git, but for your database structure instead of code.

## The Alembic Files Explained

### 1. `alembic.ini` - Configuration File
**What it does:** Main configuration for Alembic
- Tells Alembic where to find migration scripts
- Configures database connection (we override this in `env.py`)
- Settings for how migrations are named and organized

**You rarely edit this** - it's mostly configuration.

### 2. `alembic/env.py` - Migration Environment
**What it does:** The "brain" of Alembic
- Connects to your database
- Imports your models so Alembic knows what tables should exist
- Handles running migrations (upgrade/downgrade)
- Converts async database URL to sync (Alembic needs sync)

**Key parts:**
```python
from app.models import *  # Import all models so Alembic can detect them
target_metadata = Base.metadata  # Tells Alembic what the database should look like
```

### 3. `alembic/versions/` - Migration Scripts
**What it does:** Contains all your migration files
- Each file is a version of your database schema
- Files are named like: `5ab6276b6556_initial_migration_create_all_tables.py`
- Each has an `upgrade()` function (apply changes) and `downgrade()` function (undo changes)

**Example from your migration:**
```python
def upgrade() -> None:
    op.create_table('users',  # Creates the users table
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        # ... more columns
    )
    
def downgrade() -> None:
    op.drop_table('users')  # Removes the users table
```

### 4. `alembic/script.py.mako` - Template
**What it does:** Template for generating new migration files
- When you run `alembic revision`, it uses this template
- You rarely need to edit this

## How It Works in Practice

### Creating Your First Migration (What We Did)
```bash
# Alembic compared your models to the database
# Found that no tables existed
# Generated a migration to create all tables
alembic revision --autogenerate -m "Initial migration - create all tables"
```

This created `5ab6276b6556_initial_migration_create_all_tables.py` with all the `CREATE TABLE` statements.

### Applying the Migration
```bash
# This actually runs the upgrade() function
# Creates all tables in your database
alembic upgrade head
```

### Future Scenario: Adding a Column

**Step 1:** Update your model in `app/models.py`:
```python
class User(Base):
    # ... existing fields ...
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
```

**Step 2:** Generate migration:
```bash
alembic revision --autogenerate -m "Add phone_number to users"
```

**Step 3:** Review the generated migration file (Alembic creates it automatically)

**Step 4:** Apply it:
```bash
alembic upgrade head
```

Now everyone who runs `alembic upgrade head` gets the new column!

## Why This is Important

### ✅ Version Control for Database
- Track every change to your database structure
- See history of what changed and when
- Roll back if needed

### ✅ Team Collaboration
- Everyone's database stays in sync
- New team members can set up the database easily
- No more "it works on my machine" database issues

### ✅ Production Deployments
- Deploy database changes safely
- Know exactly what version the production DB is at
- Can roll back if deployment fails

### ✅ Reproducibility
- Anyone can recreate the exact database structure
- Works the same in dev, staging, and production

## Common Alembic Commands

```bash
# Create a new migration (auto-detect changes)
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# See current database version
alembic current

# See migration history
alembic history

# Show what migrations would be applied
alembic upgrade head --sql
```

## The `alembic_version` Table

When you run migrations, Alembic creates a special table called `alembic_version` that stores:
- Which migration version your database is currently at
- This lets Alembic know what's already been applied

You can see it in TablePlus - it just has one row showing the current version.

## Summary

**Alembic = Git for your database schema**

- **alembic.ini**: Configuration
- **alembic/env.py**: How to connect and what models exist
- **alembic/versions/**: All your migration scripts (database change history)
- **alembic/script.py.mako**: Template for new migrations

**Without Alembic:** You'd manually write SQL, hope everyone runs it, and have no way to track changes.

**With Alembic:** Automated, version-controlled, reproducible database changes! 🎉

