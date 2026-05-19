# Backend Startup Guide

## Quick Fix - Run Backend Properly

### Step 1: Navigate to Backend
```bash
cd backend
```

### Step 2: Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Run Backend
```bash
python run.py
```

Or alternatively:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Expected Output
```
Starting GitHub PR Intelligence Dashboard Backend...
Server will be available at http://localhost:8000
API docs at http://localhost:8000/docs

INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## Verify Backend is Running
- Open http://localhost:8000/health in browser
- Should see: `{"status":"ok"}`

## If Backend Still Won't Start

### Check 1: Virtual Environment
```bash
# Make sure venv is activated (you should see (venv) in terminal)
python --version  # Should show Python 3.8+
```

### Check 2: Dependencies
```bash
pip list | grep -i fastapi
pip list | grep -i sqlalchemy
```

### Check 3: Reinstall Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Check 4: Delete Database and Try Again
```bash
rm pr_dashboard.db
python run.py
```

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:** Make sure virtual environment is activated and dependencies are installed
```bash
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution:** Kill the process using port 8000 or use a different port
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Issue: "Database is locked"
**Solution:** Delete the database file and restart
```bash
rm pr_dashboard.db
python run.py
```

## Next Steps

Once backend is running:
1. Open http://localhost:8000/docs to see API documentation
2. In another terminal, start frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000 in browser
4. Start analyzing repositories!

## API Endpoints

- `GET /health` - Health check
- `POST /api/analyze` - Analyze repository
- `GET /api/kpi/{repo_id}` - Get KPI metrics
- `GET /api/oldest-prs/{repo_id}` - Get oldest PRs
- `GET /api/slowest-prs/{repo_id}` - Get slowest PRs
- `GET /api/contributor-activity/{repo_id}` - Get contributors
- `GET /api/monthly-flow/{repo_id}` - Get monthly flow
- `GET /api/throughput/{repo_id}` - Get throughput

## API Documentation
Visit http://localhost:8000/docs for interactive API documentation
