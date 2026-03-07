# Deployment Guide: Surgical Consult Agent with Live API

This guide covers deploying the updated Surgical Consult Agent with:
- Flask backend API for real-time Claude streaming
- Supabase integration for session persistence
- Interactive demo with editable exam findings
- Mobile-responsive design

## Prerequisites

- Python 3.10+
- Node.js 18+ (optional, for frontend development)
- Supabase account (free tier available)
- Anthropic API key

## Local Development Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `anthropic` — Claude API client
- `flask` — Web framework
- `flask-cors` — CORS handling
- `supabase` — Supabase Python client
- `python-dotenv` — Environment variable management
- `requests` — HTTP client

### 2. Configure Environment Variables

Edit `.env` with:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
FLASK_ENV=development
```

Get Supabase credentials from:
1. Create a project at https://supabase.com
2. Go to Settings > API
3. Copy the URL and `anon` key

### 3. Run the Flask Backend

```bash
python api.py
```

The API will start on `http://localhost:5000`

Verify with:
```bash
curl http://localhost:5000/api/health
```

Should return: `{"status": "ok", "message": "Surgical Consult Agent API is running"}`

### 4. Serve the Frontend

In a separate terminal, navigate to the `web/` directory and serve:

```bash
cd web
python -m http.server 8000
```

Or use any HTTP server (nginx, apache, etc.)

Visit `http://localhost:8000/index.html`

## API Endpoints

The Flask backend exposes these endpoints:

### Health Check
- **GET** `/api/health`
- Returns server status

### Session Management
- **POST** `/api/session` — Create or retrieve a session
- **GET** `/api/session/history?session_id=XXX` — Get consult history for a session

### Consult Workflow (Streaming)
All return `text/event-stream` for real-time streaming:

- **POST** `/api/consult/triage` — Generate triage analysis
- **POST** `/api/consult/context` — Generate context and gaps analysis
- **POST** `/api/consult/plan` — Generate assessment and plan
- **POST** `/api/consult/note` — Generate final consult note

### Data Persistence
- **POST** `/api/consult/save` — Save a completed consult to Supabase

## Frontend Integration

The frontend (`web/app.js`) automatically:
1. Creates a unique session ID (stored in localStorage)
2. Loads session history from Supabase
3. Calls API endpoints with user input
4. Streams responses and displays them with typing animation
5. Allows users to edit exam findings and regenerate outputs

**Key Functions:**
- `initSession()` — Initialize or retrieve user session
- `loadCase(caseName)` — Load a demo case
- `streamStageFromAPI(stageName, caseData)` — Stream a stage from the API
- `loadSessionHistory()` — Retrieve user's recent consults

## Production Deployment

### Option 1: Heroku

1. Create a `Procfile`:
```
web: gunicorn api:app
```

2. Create `runtime.txt`:
```
python-3.11.7
```

3. Deploy:
```bash
heroku login
heroku create your-app-name
heroku config:set ANTHROPIC_API_KEY=xxx
heroku config:set VITE_SUPABASE_URL=xxx
heroku config:set VITE_SUPABASE_ANON_KEY=xxx
git push heroku main
```

### Option 2: Vercel (Backend) + GitHub Pages (Frontend)

**Backend:**
- Use Vercel's `/api` serverless functions
- Convert Flask routes to serverless functions

**Frontend:**
- Deploy to GitHub Pages
- Update `API_ENDPOINTS` in `app.js` to point to Vercel backend

### Option 3: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=api.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api:app"]
```

Build and run:
```bash
docker build -t consult-agent .
docker run -p 5000:5000 -e ANTHROPIC_API_KEY=xxx consult-agent
```

## Database Migrations

The Supabase schema was created during setup. To verify:

1. Go to Supabase dashboard
2. Click "SQL Editor"
3. Run:
```sql
SELECT * FROM consult_sessions;
SELECT * FROM consult_history;
```

To reset the database:
```sql
DROP TABLE IF EXISTS consult_history;
DROP TABLE IF EXISTS consult_sessions;
```

Then re-run the migration.

## Troubleshooting

### API Returns 405 Error
- Ensure Flask app is running on the correct port
- Check CORS headers in `api.py`

### Supabase Connection Fails
- Verify credentials in `.env`
- Check Supabase project is active
- Ensure RLS policies allow access

### Streaming Not Working
- Check browser supports Fetch API with `getReader()`
- Modern browsers (Chrome 60+, Firefox 55+, Safari 10+) required
- Check network tab for API call details

### Claude API Errors
- Verify Anthropic API key is valid
- Check account has API credits
- Ensure request doesn't exceed 4096 tokens

## Performance Optimization

### Frontend
- Compress JavaScript and CSS for production
- Use HTTP/2 server push for critical assets
- Enable gzip compression

### Backend
- Use Gunicorn with multiple workers: `gunicorn --workers 4 api:app`
- Enable caching for demo case JSON files
- Use connection pooling for Supabase

### Database
- Add indexes on frequently queried columns (already done)
- Implement query caching for session history
- Archive old consults to a separate table

## Security Considerations

### API Keys
- Never commit `.env` to version control
- Use environment variables for all secrets
- Rotate API keys regularly

### Database
- RLS policies restrict access by session_id
- No sensitive patient data stored (demo only)
- For production: implement proper authentication

### Frontend
- Store session ID in localStorage (anonymous, no auth)
- For production: implement user authentication
- Add CSRF tokens for form submissions

## Monitoring

### Logs
- Flask logs to console (implement proper logging system)
- Monitor Anthropic API usage: https://console.anthropic.com
- Check Supabase metrics: Supabase dashboard > Logs

### Errors
- Implement error tracking (Sentry, LogRocket, etc.)
- Monitor API response times
- Track conversion rates (users completing consults)

## Next Steps

1. **Video Walkthrough** — Record a 2-minute demo (see `VIDEO_GUIDE.md`)
2. **Testimonials** — Get feedback from residents/clinicians
3. **Performance Testing** — Load test with concurrent users
4. **Security Audit** — Review OWASP Top 10 compliance
5. **Analytics** — Track usage patterns and user feedback
