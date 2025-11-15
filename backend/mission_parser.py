"""
Mission log parser - converts JSON logs to structured data
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from models import MissionLog, MissionEvent


class MissionLogParser:
    """Parses JSON mission logs into structured format"""

    @staticmethod
    def parse_timestamp(ts: Any) -> datetime:
        """Parse various timestamp formats"""
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            # Try common formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%m/%d/%Y %H:%M:%S",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(ts, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Could not parse timestamp: {ts}")
        if isinstance(ts, (int, float)):
            # Assume Unix timestamp
            return datetime.fromtimestamp(ts)
        raise ValueError(f"Unknown timestamp format: {ts}")

    @staticmethod
    def parse_event(event_data: Dict[str, Any]) -> MissionEvent:
        """Parse a single event from JSON"""
        return MissionEvent(
            timestamp=MissionLogParser.parse_timestamp(event_data["timestamp"]),
            event_type=event_data.get("event_type", "unknown"),
            description=event_data.get("description", ""),
            tracking_number=event_data.get("tracking_number"),
            speed=event_data.get("speed"),
            course=event_data.get("course"),
            latitude=event_data.get("latitude"),
            longitude=event_data.get("longitude"),
            metadata=event_data.get("metadata", {})
        )

    @classmethod
    def parse_json_file(cls, file_path: Path) -> MissionLog:
        """Parse a JSON mission log file"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        return cls.parse_json_data(data)

    @classmethod
    def parse_json_data(cls, data: Dict[str, Any]) -> MissionLog:
        """Parse mission log from JSON data"""
        events = [cls.parse_event(event) for event in data.get("events", [])]

        return MissionLog(
            mission_id=data.get("mission_id", "unknown"),
            mission_name=data.get("mission_name", "Unnamed Mission"),
            start_time=cls.parse_timestamp(data["start_time"]),
            end_time=cls.parse_timestamp(data["end_time"]) if "end_time" in data else None,
            vessel_name=data.get("vessel_name", "Unknown Vessel"),
            events=events,
            raw_data=data
        )

    @staticmethod
    def generate_sample_mission_log() -> Dict[str, Any]:
        """Generate a sample mission log for testing"""
        return {
            "mission_id": "MISSION-2024-001",
            "mission_name": "Training Exercise Alpha",
            "vessel_name": "USS Example",
            "start_time": "2024-11-14T08:00:00Z",
            "end_time": "2024-11-14T16:00:00Z",
            "events": [
                {
                    "timestamp": "2024-11-14T08:00:00Z",
                    "event_type": "mission_start",
                    "description": "Mission commenced",
                    "speed": 0.0,
                    "course": 0.0,
                    "latitude": 36.8529,
                    "longitude": -76.2999
                },
                {
                    "timestamp": "2024-11-14T08:15:00Z",
                    "event_type": "speed_change",
                    "description": "Increased speed to 15 knots",
                    "speed": 15.0,
                    "course": 90.0,
                    "tracking_number": "TRK-001"
                },
                {
                    "timestamp": "2024-11-14T09:30:00Z",
                    "event_type": "contact_detection",
                    "description": "Surface contact detected bearing 045",
                    "tracking_number": "TRK-002",
                    "metadata": {
                        "bearing": 45,
                        "range": 5000,
                        "classification": "merchant"
                    }
                },
                {
                    "timestamp": "2024-11-14T10:00:00Z",
                    "event_type": "course_change",
                    "description": "Changed course to 120 degrees",
                    "speed": 15.0,
                    "course": 120.0,
                    "tracking_number": "TRK-001"
                },
                {
                    "timestamp": "2024-11-14T12:00:00Z",
                    "event_type": "speed_change",
                    "description": "Reduced speed to 5 knots for man overboard drill",
                    "speed": 5.0,
                    "course": 120.0,
                    "tracking_number": "TRK-001"
                },
                {
                    "timestamp": "2024-11-14T16:00:00Z",
                    "event_type": "mission_end",
                    "description": "Mission completed, returning to port",
                    "speed": 10.0,
                    "course": 270.0
                }
            ]
        }


if __name__ == "__main__":
    # Test the parser
    sample_log = MissionLogParser.generate_sample_mission_log()
    mission = MissionLogParser.parse_json_data(sample_log)
    print(f"Parsed mission: {mission.mission_name}")
    print(f"Events: {len(mission.events)}")
    for event in mission.events:
        print(f"  - {event.timestamp}: {event.description}")
