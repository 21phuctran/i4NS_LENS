"""
FastAPI server for i4NS LENS
Provides REST API for mission log upload, analysis, and chat
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    MissionLog, MissionAnalysis, ChatQuery, ChatResponse,
    ComparisonResult
)
from mission_parser import MissionLogParser
from rag_pipeline import MissionAnalysisRAG
from doctrine_indexer import DoctrineIndexer, LocalEmbeddings
from config import MISSION_LOGS_DIR, DOCTRINES_DIR

# Initialize FastAPI app
app = FastAPI(
    title="i4NS LENS API",
    description="Lessons Learned Enhancement System for Naval Operations",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
rag_pipeline: Optional[MissionAnalysisRAG] = None
doctrine_indexer: Optional[DoctrineIndexer] = None
stored_analyses: dict = {}  # In-memory storage for demo (use DB in production)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global rag_pipeline, doctrine_indexer

    print("Initializing i4NS LENS...")

    # Initialize doctrine indexer
    embeddings = LocalEmbeddings()
    doctrine_indexer = DoctrineIndexer(embeddings)

    # Check if doctrine documents exist, create sample if not
    if not any(DOCTRINES_DIR.glob("*.txt")) and not any(DOCTRINES_DIR.glob("*.pdf")):
        print("No doctrine documents found. Creating sample doctrine...")
        doctrine_indexer.create_sample_doctrine()

    # Index doctrines
    print("Indexing doctrine documents...")
    doctrine_indexer.index_doctrines()

    # Initialize RAG pipeline
    print("Initializing RAG pipeline...")
    rag_pipeline = MissionAnalysisRAG(use_local_llm=True)

    print("i4NS LENS ready!")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "operational",
        "service": "i4NS LENS",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "rag_pipeline": rag_pipeline is not None,
        "doctrine_indexer": doctrine_indexer is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/missions/upload", response_model=dict)
async def upload_mission_log(file: UploadFile = File(...)):
    """
    Upload a mission log JSON file
    """
    try:
        # Read file content
        content = await file.read()
        data = json.loads(content)

        # Parse mission log
        mission = MissionLogParser.parse_json_data(data)

        # Save to disk
        save_path = MISSION_LOGS_DIR / f"{mission.mission_id}.json"
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)

        return {
            "success": True,
            "mission_id": mission.mission_id,
            "mission_name": mission.mission_name,
            "events_count": len(mission.events),
            "message": "Mission log uploaded successfully"
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/api/missions/analyze", response_model=MissionAnalysis)
async def analyze_mission(mission_data: dict):
    """
    Analyze a mission log against doctrine
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")

    try:
        # Parse mission log
        mission = MissionLogParser.parse_json_data(mission_data)

        # Run analysis
        analysis = rag_pipeline.analyze_mission(mission)

        # Store analysis
        stored_analyses[mission.mission_id] = analysis

        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing mission: {str(e)}")


@app.get("/api/missions/{mission_id}/analysis", response_model=MissionAnalysis)
async def get_mission_analysis(mission_id: str):
    """
    Get stored analysis for a mission
    """
    if mission_id not in stored_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return stored_analyses[mission_id]


@app.get("/api/missions", response_model=List[dict])
async def list_missions():
    """
    List all uploaded mission logs
    """
    missions = []

    for log_file in MISSION_LOGS_DIR.glob("*.json"):
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
                mission = MissionLogParser.parse_json_data(data)
                missions.append({
                    "mission_id": mission.mission_id,
                    "mission_name": mission.mission_name,
                    "vessel_name": mission.vessel_name,
                    "start_time": mission.start_time.isoformat(),
                    "events_count": len(mission.events),
                    "has_analysis": mission.mission_id in stored_analyses
                })
        except Exception as e:
            print(f"Error loading {log_file}: {e}")
            continue

    return missions


@app.post("/api/chat", response_model=ChatResponse)
async def chat(query: ChatQuery):
    """
    Ask questions about missions or doctrines
    """
    if doctrine_indexer is None:
        raise HTTPException(status_code=503, detail="Doctrine indexer not initialized")

    try:
        # Search for relevant doctrine passages
        relevant_docs = doctrine_indexer.search(query.question, k=5)

        # For now, simple response with sources
        # In production, use LLM to generate answer
        sources = [doc.metadata.get("source_file", "Unknown") for doc in relevant_docs]

        # Simple answer construction (enhance with LLM in production)
        answer_parts = [
            f"Based on doctrine documents, here are relevant passages:",
            "",
        ]

        for i, doc in enumerate(relevant_docs[:3], 1):
            answer_parts.append(f"{i}. {doc.page_content[:200]}...")
            answer_parts.append("")

        answer = "\n".join(answer_parts)

        return ChatResponse(
            answer=answer,
            sources=list(set(sources))
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/api/sample/mission")
async def get_sample_mission():
    """
    Get a sample mission log for testing
    """
    sample = MissionLogParser.generate_sample_mission_log()
    return sample


@app.post("/api/doctrines/reindex")
async def reindex_doctrines():
    """
    Force reindex of doctrine documents
    """
    global doctrine_indexer, rag_pipeline

    try:
        if doctrine_indexer is None:
            embeddings = LocalEmbeddings()
            doctrine_indexer = DoctrineIndexer(embeddings)

        doctrine_indexer.index_doctrines(force_reindex=True)

        # Reinitialize RAG pipeline with new index
        rag_pipeline = MissionAnalysisRAG(use_local_llm=True)

        return {
            "success": True,
            "message": "Doctrine documents reindexed successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("Starting i4NS LENS API Server...")
    print("Access at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
