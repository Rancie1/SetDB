# Environment Variables Setup Guide

You need to create a `.env` file in the `backend/` directory with the following configuration.

## Required Variables

### 1. DATABASE_URL
**Required** - PostgreSQL database connection string

```
DATABASE_URL=postgresql://username:password@localhost:5432/deckd
```

**How to set it up:**
- Install PostgreSQL if you haven't already
- Create a database named `deckd`:
  ```sql
  CREATE DATABASE deckd;
  ```
- Replace `username` and `password` with your PostgreSQL credentials
- If using a different host/port, adjust accordingly

**Example:**
```
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/deckd
```

### 2. JWT_SECRET
**Required** - Secret key for signing JWT tokens

```
JWT_SECRET=your-secret-key-here
```

**How to generate a secure secret:**
```bash
# Using OpenSSL (recommended)
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Important:** Use a long, random string. Never commit this to version control!

## Optional Variables (with defaults)

### 3. JWT_ALGORITHM
**Optional** - Default: `HS256`
```
JWT_ALGORITHM=HS256
```

### 4. JWT_EXPIRATION_HOURS
**Optional** - Default: `24`
```
JWT_EXPIRATION_HOURS=24
```

## External API Keys (Optional)

### 5. YOUTUBE_API_KEY
**Optional** - Required for importing sets from YouTube

**How to get it:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "YouTube Data API v3"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy the API key

```
YOUTUBE_API_KEY=your-youtube-api-key-here
```

**Note:** YouTube API has free quota limits. For production, consider setting up billing.

### 6. SOUNDCLOUD_CLIENT_ID
**Optional** - For advanced SoundCloud features

The basic SoundCloud import uses oEmbed API which doesn't require authentication.
This is only needed if you want to use SoundCloud's full API.

```
SOUNDCLOUD_CLIENT_ID=your-soundcloud-client-id-here
```

## Complete .env File Example

Create a file named `.env` in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/deckd

# JWT Authentication
JWT_SECRET=your-generated-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs (optional)
YOUTUBE_API_KEY=your-youtube-api-key
SOUNDCLOUD_CLIENT_ID=your-soundcloud-client-id
```

## Quick Setup Commands

```bash
# Generate JWT secret
openssl rand -hex 32

# Create .env file (copy and edit the values)
cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/deckd
JWT_SECRET=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
YOUTUBE_API_KEY=
SOUNDCLOUD_CLIENT_ID=
EOF
```

## Security Notes

- **Never commit `.env` to version control** - it's already in `.gitignore`
- Use strong, random values for `JWT_SECRET`
- In production, use environment variables or a secrets manager
- Keep your API keys secure and rotate them regularly

