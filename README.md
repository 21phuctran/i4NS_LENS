# i4NS LENS - Lessons Learned Enhancement System

**Intelligent Insights for Naval Service - Lessons Enhancement & Navigation System**

A RAG-powered application designed to enhance the U.S. Navy's Lessons Learned process by automatically analyzing mission logs against naval doctrine and generating actionable insights.

## 🎯 Overview

i4NS LENS helps naval personnel:
- **Upload mission logs** in JSON format
- **Analyze actions** against Navy doctrine requirements
- **Identify compliance gaps** with timestamp precision
- **Generate lessons learned** automatically
- **Query insights** through an interactive chat interface

Built for **offline deployment** on ships with no internet access.

## 🏗️ Architecture

```
Frontend (React)
    ↓
FastAPI Backend
    ↓
LangGraph RAG Pipeline
    ↓
├─ Mission Log Parser
├─ Doctrine Vector Store (FAISS)
├─ Comparison Engine
└─ Local LLM (Optional)
```

## 📋 Features

### Frame 1: Upload Interface
- Drag-and-drop mission log upload
- Sample mission for testing
- LLM processing trigger

### Frame 2: Analysis Dashboard
- **Previous Missions**: Historical mission list with compliance scores
- **Timeline View**: Timestamp-based event analysis
- **Doctrine Comparison**: Expected vs. Actual actions
- **Lessons Learned**: Auto-generated insights
- **Recommendations**: Actionable next steps
- **Chat Interface**: Ask questions about missions and doctrine

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) Python 3.11+ for local development
- (Optional) Node.js 18+ for frontend development

### Option 1: Docker Deployment (Recommended for Ships)

1. **Clone the repository**
```bash
git clone <repository-url>
cd i4NS_LENS
```

2. **Add doctrine documents**
```bash
# Place your Navy doctrine PDFs/text files in:
mkdir -p data/doctrines
# Copy your doctrine files here
```

3. **Build and run**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup

1. **Install Python dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Create sample doctrine (optional)**
```bash
python doctrine_indexer.py
```

3. **Start the API server**
```bash
python api.py
```

#### Frontend Setup

1. **Install Node dependencies**
```bash
cd frontend
npm install
```

2. **Start development server**
```bash
npm run dev
```

3. **Access at** http://localhost:3000

## 📁 Mission Log Format

Mission logs should be JSON files with this structure:

```json
{
  "mission_id": "MISSION-2024-001",
  "mission_name": "Training Exercise Alpha",
  "vessel_name": "USS Example",
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

### Event Types
- `mission_start` - Mission commencement
- `mission_end` - Mission completion
- `speed_change` - Vessel speed changes
- `course_change` - Course adjustments
- `contact_detection` - Surface contact detection
- `man_overboard` - Man overboard events
- (Add custom event types as needed)

## 🔧 Configuration

### Backend Configuration
Edit `backend/config.py`:

```python
# Embedding model (must be available offline)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# LLM Configuration
USE_LOCAL_LLM = True  # Set to False to use OpenAI API
LOCAL_LLM_MODEL = "llama2"  # Ollama model name

# Vector store settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

### Adding Doctrine Documents

1. Place PDF or text files in `data/doctrines/`
2. Reindex via API:
```bash
curl -X POST http://localhost:8000/api/doctrines/reindex
```

Or use the provided sample doctrine:
```bash
python backend/doctrine_indexer.py
```

## 📊 API Endpoints

### Mission Operations
- `POST /api/missions/upload` - Upload mission log
- `POST /api/missions/analyze` - Analyze mission
- `GET /api/missions` - List all missions
- `GET /api/missions/{mission_id}/analysis` - Get analysis

### Doctrine Operations
- `POST /api/doctrines/reindex` - Reindex doctrine documents

### Chat
- `POST /api/chat` - Ask questions

### System
- `GET /api/health` - Health check
- `GET /api/sample/mission` - Get sample mission

Full API documentation available at `/docs` when server is running.

## 🗂️ Project Structure

```
i4NS_LENS/
├── backend/
│   ├── api.py                 # FastAPI server
│   ├── config.py              # Configuration
│   ├── models.py              # Data models
│   ├── mission_parser.py      # JSON log parser
│   ├── doctrine_indexer.py    # Document indexing
│   ├── rag_pipeline.py        # LangGraph RAG pipeline
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadFrame.jsx
│   │   │   ├── DashboardFrame.jsx
│   │   │   └── *.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── doctrines/             # Doctrine PDFs/text files
│   ├── mission_logs/          # Uploaded mission logs
│   └── vector_store/          # FAISS index
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔒 Offline Deployment

This system is designed to run completely offline on Navy vessels:

1. **Pre-download all models**: The Docker image includes the embedding model
2. **Local vector store**: FAISS runs entirely locally
3. **No external API calls**: All processing happens on-device
4. **Persistent storage**: Mission logs and doctrine index are saved to volumes

### Preparing for Offline Deployment

1. **Build the Docker image** on a machine with internet:
```bash
docker-compose build
```

2. **Save the image**:
```bash
docker save i4ns-lens:latest | gzip > i4ns-lens.tar.gz
```

3. **Transfer to ship** via approved secure media

4. **Load on ship**:
```bash
docker load < i4ns-lens.tar.gz
docker-compose up -d
```

## 🧪 Testing

### Test with Sample Mission
```bash
# Via API
curl -X GET http://localhost:8000/api/sample/mission

# Via UI
Click "Run LLM (Sample Mission)" button
```

### Manual Testing
1. Upload mission log JSON file
2. Review analysis dashboard
3. Check timeline events
4. Verify doctrine comparisons
5. Test chat interface

## 🛠️ Development

### Running Tests
```bash
cd backend
pytest
```

### Code Structure
- **Models** (`models.py`): Pydantic models for type safety
- **Parser** (`mission_parser.py`): Converts JSON → structured data
- **Indexer** (`doctrine_indexer.py`): Handles doctrine embedding/retrieval
- **RAG Pipeline** (`rag_pipeline.py`): LangGraph workflow for analysis
- **API** (`api.py`): REST endpoints

### Adding New Features

1. **New event types**: Update `mission_parser.py` and `rag_pipeline.py`
2. **Custom analysis logic**: Modify `rag_pipeline._analyze_event_against_doctrine()`
3. **UI enhancements**: Edit React components in `frontend/src/components/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

Built for the U.S. Navy to enhance operational effectiveness through AI-powered lessons learned analysis.

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

**Status**: Development Version 1.0.0
**Last Updated**: November 2024