# Setup Guide for i4NS LENS

## Initial Setup (First Time)

### 1. Create Data Directories
```bash
mkdir -p data/doctrines data/mission_logs data/vector_store logs
```

### 2. Add Doctrine Documents (Important!)

The system needs Navy doctrine documents to compare mission actions against. You have two options:

#### Option A: Use Sample Doctrine (For Testing)
```bash
cd backend
python doctrine_indexer.py
```

This creates a sample naval doctrine document in `data/doctrines/sample_naval_doctrine.txt`.

#### Option B: Add Real Doctrine Documents
1. Place your Navy doctrine PDFs or text files in `data/doctrines/`
2. The system will automatically index them on startup

### 3. Install Dependencies

#### For Docker Deployment (Recommended)
```bash
# Just build the Docker image - it includes everything
docker-compose build
```

#### For Local Development
**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

## Running the Application

### Option 1: Docker (Production/Offline Deployment)

Start everything:
```bash
docker-compose up
```

Or run in background:
```bash
docker-compose up -d
```

Stop:
```bash
docker-compose down
```

Access at: http://localhost:8000

### Option 2: Local Development

**Terminal 1 - Backend:**
```bash
cd backend
python api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000 (frontend) and http://localhost:8000 (API)

## First Time Usage

### 1. Test with Sample Mission

The easiest way to test the system:

1. Open http://localhost:8000 (or :3000 for local dev)
2. Click **"Run LLM (Sample Mission)"** button
3. Wait for analysis to complete
4. Explore the dashboard with timeline, comparisons, and chat

### 2. Upload Your Own Mission Log

Create a JSON file following this format:

```json
{
  "mission_id": "MISSION-2024-001",
  "mission_name": "Your Mission Name",
  "vessel_name": "Your Vessel",
  "start_time": "2024-11-14T08:00:00Z",
  "end_time": "2024-11-14T16:00:00Z",
  "events": [
    {
      "timestamp": "2024-11-14T08:15:00Z",
      "event_type": "speed_change",
      "description": "Increased speed to 15 knots",
      "speed": 15.0,
      "course": 90.0,
      "tracking_number": "TRK-001"
    }
  ]
}
```

Then drag and drop it into the upload area.

## Verifying Installation

### Check API Health
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "rag_pipeline": true,
  "doctrine_indexer": true,
  "timestamp": "2024-11-14T..."
}
```

### List Available Endpoints
Open in browser: http://localhost:8000/docs

This shows interactive API documentation.

## Common Issues

### Issue: "No doctrine documents found"
**Solution:** Add doctrine PDFs/text files to `data/doctrines/` or run:
```bash
python backend/doctrine_indexer.py
```

### Issue: Port 8000 already in use
**Solution:** Change port in `docker-compose.yml` or stop other services using port 8000

### Issue: Frontend can't connect to backend
**Solution:**
- Check backend is running on port 8000
- For local dev, ensure proxy is configured in `frontend/vite.config.js`

### Issue: Slow analysis/timeout
**Solution:**
- Embedding model needs to download on first run (requires internet)
- For offline deployment, pre-build Docker image on internet-connected machine

## Offline Deployment Checklist

For deploying on ships without internet:

- [ ] Build Docker image on internet-connected machine
- [ ] Download embedding model (happens automatically during build)
- [ ] Add all doctrine documents to `data/doctrines/`
- [ ] Test locally before transfer
- [ ] Save Docker image: `docker save i4ns-lens:latest | gzip > i4ns-lens.tar.gz`
- [ ] Transfer image file via approved secure media
- [ ] Load on ship: `docker load < i4ns-lens.tar.gz`
- [ ] Run: `docker-compose up -d`

## Next Steps

1. **Add Real Doctrine**: Replace sample with actual Navy doctrine documents
2. **Test Mission Logs**: Upload real mission logs
3. **Customize Event Types**: Edit `mission_parser.py` for your specific event types
4. **Adjust Analysis Logic**: Modify `rag_pipeline.py` for custom compliance rules
5. **Train Users**: Show crew how to format mission logs properly

## Support

For questions or issues:
- Check the main [README.md](README.md)
- Review API docs at `/docs`
- Check backend logs: `docker-compose logs -f` (Docker) or console output (local)

---

**Quick Reference:**
- Frontend: http://localhost:8000 (Docker) or http://localhost:3000 (local)
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health
