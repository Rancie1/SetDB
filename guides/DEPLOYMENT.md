# Deployment Guide

This guide covers deploying the Deckd backend to various platforms.

## Prerequisites

- PostgreSQL database (managed or self-hosted)
- Environment variables configured
- Database migrations run

## Environment Variables

Set these in your deployment platform:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
JWT_SECRET=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# Optional external APIs
YOUTUBE_API_KEY=your-youtube-api-key
SOUNDCLOUD_CLIENT_ID=your-soundcloud-client-id
SOUNDCLOUD_CLIENT_SECRET=your-soundcloud-client-secret
SOUNDCLOUD_REDIRECT_URI=https://your-frontend-domain.com/auth/soundcloud/callback
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
```

## Option 1: Railway (Recommended for Simplicity)

**Best for**: Quick deployment, PostgreSQL included, free tier available

### Steps:

1. **Sign up** at [railway.app](https://railway.app)

2. **Create a new project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo" (connect your repo)
   - Or "Empty Project" and connect later

3. **Add PostgreSQL**:
   - Click "+ New" → "Database" → "Add PostgreSQL"
   - Railway will auto-create `DATABASE_URL` env var

4. **Deploy Backend**:
   - Click "+ New" → "GitHub Repo" → Select your repo
   - Set root directory to `backend/`
   - Railway will auto-detect Python and install dependencies
   - The `Procfile` or `railway.json` will be used

5. **Set Environment Variables**:
   - Go to your service → "Variables"
   - Add all required env vars (see above)
   - **Important**: Set `CORS_ORIGINS` to your frontend URL(s)

6. **Run Migrations**:
   - Go to service → "Deployments" → Click on latest deployment
   - Open "Deploy Logs" → Click "Shell"
   - Run: `alembic upgrade head`

7. **Get Your URL**:
   - Railway provides a URL like `https://your-app.up.railway.app`
   - Use this as your backend API URL

### Railway-Specific Notes:

- **Port**: Railway sets `PORT` env var automatically
- **Build**: Uses `requirements.txt` automatically
- **Start Command**: Uses `Procfile` or detects `uvicorn app.main:app`
- **PostgreSQL**: Managed database included, connection string auto-set

---

## Option 2: Render

**Best for**: Free tier, easy setup, PostgreSQL included

### Steps:

1. **Sign up** at [render.com](https://render.com)

2. **Create PostgreSQL Database**:
   - Dashboard → "New +" → "PostgreSQL"
   - Copy the "Internal Database URL" (you'll need it)

3. **Create Web Service**:
   - Dashboard → "New +" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - **Name**: `deckd-backend`
     - **Root Directory**: `backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Free (or paid for better performance)

4. **Set Environment Variables**:
   - Go to "Environment" tab
   - Add all required vars
   - Set `DATABASE_URL` to the PostgreSQL internal URL
   - Set `CORS_ORIGINS` to your frontend URL

5. **Run Migrations**:
   - Go to "Shell" tab
   - Run: `alembic upgrade head`

6. **Get Your URL**:
   - Render provides: `https://your-app.onrender.com`

### Render-Specific Notes:

- **Free Tier**: Spins down after 15min inactivity (first request may be slow)
- **PostgreSQL**: Free tier available (90-day retention)
- **Auto-Deploy**: Deploys on git push to main branch

---

## Option 3: Fly.io

**Best for**: Global edge deployment, good performance, Docker-based

### Steps:

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**:
   ```bash
   fly auth login
   ```

3. **Create Dockerfile** (if not exists):
   ```dockerfile
   FROM python:3.12-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8080
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

4. **Launch App**:
   ```bash
   cd backend
   fly launch
   ```
   - Follow prompts
   - Create PostgreSQL database when asked

5. **Set Secrets**:
   ```bash
   fly secrets set DATABASE_URL="postgresql://..."
   fly secrets set JWT_SECRET="your-secret"
   fly secrets set CORS_ORIGINS="https://your-frontend.com"
   # ... add all other secrets
   ```

6. **Run Migrations**:
   ```bash
   fly ssh console
   alembic upgrade head
   ```

7. **Deploy**:
   ```bash
   fly deploy
   ```

---

## Option 4: DigitalOcean App Platform

**Best for**: Managed platform, PostgreSQL included, scalable

### Steps:

1. **Sign up** at [digitalocean.com](https://digitalocean.com)

2. **Create App**:
   - Go to "App Platform" → "Create App"
   - Connect GitHub repo
   - Configure:
     - **Type**: Web Service
     - **Source**: `backend/`
     - **Build Command**: `pip install -r requirements.txt`
     - **Run Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add Database**:
   - "Resources" → "Add Resource" → "Database"
   - Choose PostgreSQL
   - Connection string auto-set as `DATABASE_URL`

4. **Set Environment Variables**:
   - Go to "Settings" → "App-Level Environment Variables"
   - Add all required vars

5. **Run Migrations**:
   - Use "Run Command" feature or SSH
   - Run: `alembic upgrade head`

---

## Option 5: Docker + Any Cloud Provider

**Best for**: Full control, custom infrastructure

### Create Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Compose (for local testing):

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/deckd
      - JWT_SECRET=your-secret
      - CORS_ORIGINS=http://localhost:5173
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=deckd
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Deploy to AWS/GCP/Azure:

- **AWS**: Use ECS, Elastic Beanstalk, or EC2
- **GCP**: Use Cloud Run, App Engine, or GKE
- **Azure**: Use App Service or Container Instances

---

## Production Considerations

### 1. Use Production ASGI Server

For production, use **Gunicorn with Uvicorn workers**:

```bash
pip install gunicorn
```

Update `Procfile` or start command:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

Or create `gunicorn.conf.py`:
```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
```

### 2. Environment Variables

- **Never commit** `.env` files
- Use platform secrets/environment variables
- Rotate `JWT_SECRET` regularly
- Use strong, random secrets

### 3. Database Migrations

- Run migrations as part of deployment (or manually)
- Consider migration rollback strategy
- Backup database before major migrations

### 4. CORS Configuration

- Set `CORS_ORIGINS` to your production frontend URL(s)
- Don't use `*` in production
- Include both `https://yourdomain.com` and `https://www.yourdomain.com` if needed

### 5. Monitoring & Logging

- Set up logging (platforms usually provide this)
- Monitor error rates
- Set up alerts for downtime

### 6. SSL/HTTPS

- Most platforms provide HTTPS automatically
- Ensure your frontend uses HTTPS when calling backend

### 7. Health Checks

Your app already has `/health` endpoint - configure your platform to use it:
- Health check path: `/health`
- Health check interval: 30s

---

## Post-Deployment Checklist

- [ ] Database migrations run successfully
- [ ] Environment variables set correctly
- [ ] CORS origins configured for frontend
- [ ] Health check endpoint responding (`/health`)
- [ ] API docs accessible (`/docs`)
- [ ] Test authentication endpoints
- [ ] Test database connections
- [ ] Monitor logs for errors
- [ ] Update frontend `VITE_API_URL` to production backend URL

---

## Troubleshooting

### Database Connection Issues

- Check `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Ensure database is accessible from deployment platform
- Check firewall/security group settings

### CORS Errors

- Verify `CORS_ORIGINS` includes your frontend URL
- Check for trailing slashes
- Ensure frontend uses correct backend URL

### Migration Failures

- Check database connection
- Verify Alembic version matches
- Review migration files for errors
- Consider running migrations manually via platform shell

### Port Issues

- Most platforms set `PORT` env var automatically
- Use `$PORT` or `0.0.0.0` as host
- Check platform documentation for port requirements

---

## Recommended Setup

**For most users**: **Railway** or **Render**
- Easiest setup
- PostgreSQL included
- Free tier available
- Automatic HTTPS
- Good for MVP/production

**For scale**: **Fly.io** or **DigitalOcean**
- Better performance
- Global edge deployment
- More control
- Paid plans recommended
