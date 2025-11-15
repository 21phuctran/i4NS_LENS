"""
Data models for mission logs and doctrine analysis
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MissionEvent(BaseModel):
    """Single event from a mission log"""
    timestamp: datetime
    event_type: str  # e.g., "speed_change", "course_change", "contact_detection"
    description: str
    tracking_number: Optional[str] = None
    speed: Optional[float] = None
    course: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MissionLog(BaseModel):
    """Complete mission log"""
    mission_id: str
    mission_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    vessel_name: str
    events: List[MissionEvent]
    raw_data: Optional[Dict[str, Any]] = None


class DoctrineReference(BaseModel):
    """Reference to doctrine requirements"""
    doctrine_id: str
    doctrine_name: str
    section: str
    requirement: str
    context: str  # The full context from the doctrine document


class ComparisonResult(BaseModel):
    """Comparison between actual action and doctrine requirement"""
    timestamp: datetime
    event_description: str
    actual_action: str
    expected_action: str  # What doctrine says
    compliance_status: str  # "compliant", "non-compliant", "partial", "unclear"
    doctrine_references: List[DoctrineReference]
    analysis: str  # LLM-generated analysis
    severity: Optional[str] = None  # "critical", "major", "minor", "info"


class MissionAnalysis(BaseModel):
    """Complete analysis of a mission"""
    mission_id: str
    mission_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    comparisons: List[ComparisonResult]
    summary: str
    lessons_learned: List[str]
    recommendations: List[str]
    overall_compliance_score: Optional[float] = None  # 0-100


class ChatQuery(BaseModel):
    """User question about missions or doctrines"""
    question: str
    mission_id: Optional[str] = None  # Filter to specific mission
    context_type: Optional[str] = None  # "mission", "doctrine", "both"


class ChatResponse(BaseModel):
    """Response to user question"""
    answer: str
    sources: List[str]  # Source documents used
    related_events: Optional[List[MissionEvent]] = None
