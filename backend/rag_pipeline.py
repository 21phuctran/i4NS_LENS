"""
LangGraph RAG Pipeline for Mission Analysis
Analyzes mission logs against doctrine requirements
"""

from typing import List, TypedDict, Optional
from datetime import datetime
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langgraph.graph import START, StateGraph
from langchain_community.llms import LlamaCpp

from models import (
    MissionLog, MissionEvent, ComparisonResult,
    DoctrineReference, MissionAnalysis
)
from doctrine_indexer import DoctrineIndexer, LocalEmbeddings


class AnalysisState(TypedDict):
    """State for the RAG pipeline"""
    mission_log: MissionLog
    current_event: Optional[MissionEvent]
    doctrine_context: List[Document]
    comparison_results: List[ComparisonResult]
    summary: str
    lessons_learned: List[str]
    recommendations: List[str]


class MissionAnalysisRAG:
    """RAG pipeline for analyzing mission logs against doctrine"""

    def __init__(self, use_local_llm: bool = True):
        """
        Initialize the RAG pipeline

        Args:
            use_local_llm: If True, use local LLM (Ollama/LlamaCpp).
                          If False, requires OpenAI API key (not available offline)
        """
        self.use_local_llm = use_local_llm

        # Initialize embeddings and doctrine indexer
        self.embeddings = LocalEmbeddings()
        self.doctrine_indexer = DoctrineIndexer(self.embeddings)
        self.doctrine_indexer.index_doctrines()

        # Initialize LLM (local for offline use)
        if use_local_llm:
            # For offline use - requires Ollama or a local model file
            # This is a placeholder - you'll need to configure based on your setup
            self.llm = None  # Will be initialized when needed
            print("Note: Local LLM support requires Ollama or LlamaCpp model")
        else:
            # For online use with OpenAI
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model="gpt-4o-mini")

        # Build the LangGraph workflow
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for mission analysis"""

        # Define the workflow
        graph_builder = StateGraph(AnalysisState)

        # Add nodes
        graph_builder.add_node("analyze_events", self._analyze_events_node)
        graph_builder.add_node("retrieve_doctrine", self._retrieve_doctrine_node)
        graph_builder.add_node("compare_actions", self._compare_actions_node)
        graph_builder.add_node("generate_summary", self._generate_summary_node)

        # Define the flow
        graph_builder.add_edge(START, "analyze_events")
        graph_builder.add_edge("analyze_events", "retrieve_doctrine")
        graph_builder.add_edge("retrieve_doctrine", "compare_actions")
        graph_builder.add_edge("compare_actions", "generate_summary")

        return graph_builder.compile()

    def _analyze_events_node(self, state: AnalysisState) -> dict:
        """Analyze mission events and prepare for doctrine comparison"""
        mission_log = state["mission_log"]
        comparison_results = []

        # For now, we'll analyze each event individually
        # In production, you might batch similar events
        print(f"Analyzing {len(mission_log.events)} events...")

        return {
            "comparison_results": comparison_results,
            "current_event": mission_log.events[0] if mission_log.events else None
        }

    def _retrieve_doctrine_node(self, state: AnalysisState) -> dict:
        """Retrieve relevant doctrine passages for mission events"""
        mission_log = state["mission_log"]

        # Create search queries from mission events
        event_descriptions = [
            f"{event.event_type}: {event.description}"
            for event in mission_log.events
        ]

        # Search for relevant doctrine
        all_doctrine_docs = []
        for desc in event_descriptions[:5]:  # Limit to avoid too many searches
            docs = self.doctrine_indexer.search(desc, k=3)
            all_doctrine_docs.extend(docs)

        # Remove duplicates based on content
        unique_docs = []
        seen_content = set()
        for doc in all_doctrine_docs:
            if doc.page_content not in seen_content:
                unique_docs.append(doc)
                seen_content.add(doc.page_content)

        print(f"Retrieved {len(unique_docs)} relevant doctrine passages")

        return {"doctrine_context": unique_docs}

    def _compare_actions_node(self, state: AnalysisState) -> dict:
        """Compare actual actions against doctrine requirements"""
        mission_log = state["mission_log"]
        doctrine_context = state.get("doctrine_context", [])
        comparison_results = []

        # Create a combined doctrine context string
        doctrine_text = "\n\n".join([
            f"DOCTRINE PASSAGE {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(doctrine_context)
        ])

        # Analyze each significant event
        for event in mission_log.events:
            # Create comparison using rule-based analysis and/or LLM
            comparison = self._analyze_event_against_doctrine(
                event, doctrine_text, doctrine_context
            )
            if comparison:
                comparison_results.append(comparison)

        print(f"Generated {len(comparison_results)} comparisons")

        return {"comparison_results": comparison_results}

    def _analyze_event_against_doctrine(
        self,
        event: MissionEvent,
        doctrine_text: str,
        doctrine_docs: List[Document]
    ) -> Optional[ComparisonResult]:
        """Analyze a single event against doctrine"""

        # For offline/demo mode, use rule-based analysis
        # In production with LLM, this would be more sophisticated

        # Extract doctrine requirements based on event type
        expected_action = self._get_expected_action_for_event(event, doctrine_text)
        actual_action = event.description

        # Determine compliance
        compliance_status = self._determine_compliance(event, expected_action)

        # Extract doctrine references
        doctrine_refs = [
            DoctrineReference(
                doctrine_id=doc.metadata.get("source_file", "unknown"),
                doctrine_name=doc.metadata.get("source_file", "Naval Doctrine"),
                section="General",
                requirement=doc.page_content[:200],
                context=doc.page_content
            )
            for doc in doctrine_docs[:2]  # Top 2 most relevant
        ]

        # Generate analysis
        analysis = self._generate_event_analysis(
            event, expected_action, actual_action, compliance_status
        )

        return ComparisonResult(
            timestamp=event.timestamp,
            event_description=event.description,
            actual_action=actual_action,
            expected_action=expected_action,
            compliance_status=compliance_status,
            doctrine_references=doctrine_refs,
            analysis=analysis,
            severity=self._determine_severity(compliance_status)
        )

    def _get_expected_action_for_event(
        self,
        event: MissionEvent,
        doctrine_text: str
    ) -> str:
        """Extract expected action from doctrine for this event type"""

        # Rule-based extraction based on event type
        event_type_expectations = {
            "speed_change": "Log timestamp, previous speed, new speed, reason, and tracking number. Changes > 5 knots require communication to all stations.",
            "course_change": "Log timestamp, previous course, new course, and tracking number. Notify navigation team for changes > 10 degrees.",
            "contact_detection": "Assign tracking number immediately. Log bearing, range, timestamp, and classification. Maintain continuous tracking.",
            "man_overboard": "Sound alarm, reduce speed to 5 knots, mark position with GPS timestamp, deploy recovery equipment.",
            "mission_start": "Log start time (UTC), record initial position, document objectives, verify systems.",
            "mission_end": "Log completion time, record final position, document outcomes, prepare debrief."
        }

        expected = event_type_expectations.get(
            event.event_type,
            "Follow standard operational procedures and maintain detailed logs."
        )

        # Could enhance with LLM to extract from doctrine_text
        return expected

    def _determine_compliance(
        self,
        event: MissionEvent,
        expected_action: str
    ) -> str:
        """Determine if action complies with doctrine"""

        # Simple rule-based compliance check
        # In production, use LLM for more nuanced analysis

        has_tracking = event.tracking_number is not None
        has_timestamp = event.timestamp is not None

        if event.event_type == "speed_change":
            if has_tracking and has_timestamp and event.speed is not None:
                return "compliant"
            elif has_timestamp:
                return "partial"
            else:
                return "non-compliant"

        elif event.event_type == "contact_detection":
            if has_tracking and has_timestamp:
                return "compliant"
            else:
                return "non-compliant"

        # Default to unclear if we can't determine
        return "unclear"

    def _determine_severity(self, compliance_status: str) -> str:
        """Determine severity based on compliance"""
        severity_map = {
            "compliant": "info",
            "partial": "minor",
            "non-compliant": "major",
            "unclear": "minor"
        }
        return severity_map.get(compliance_status, "minor")

    def _generate_event_analysis(
        self,
        event: MissionEvent,
        expected: str,
        actual: str,
        compliance: str
    ) -> str:
        """Generate analysis text for an event"""

        if compliance == "compliant":
            return f"Event '{event.event_type}' was properly documented with all required information including tracking number and timestamp. This follows doctrine requirements."

        elif compliance == "partial":
            return f"Event '{event.event_type}' was logged but missing some required information (e.g., tracking number). Recommend ensuring all events include complete documentation per doctrine."

        elif compliance == "non-compliant":
            return f"Event '{event.event_type}' did not meet doctrine requirements. Missing critical information such as tracking number or complete timestamp data. This should be addressed in future operations."

        else:
            return f"Unable to fully determine compliance for event '{event.event_type}'. Recommend manual review against doctrine requirements."

    def _generate_summary_node(self, state: AnalysisState) -> dict:
        """Generate overall mission summary and lessons learned"""
        comparison_results = state.get("comparison_results", [])
        mission_log = state["mission_log"]

        # Calculate compliance statistics
        total_events = len(comparison_results)
        compliant = sum(1 for c in comparison_results if c.compliance_status == "compliant")
        partial = sum(1 for c in comparison_results if c.compliance_status == "partial")
        non_compliant = sum(1 for c in comparison_results if c.compliance_status == "non-compliant")

        compliance_score = (compliant / total_events * 100) if total_events > 0 else 0

        # Generate summary
        summary = f"""Mission Analysis Summary for {mission_log.mission_name}

Total Events Analyzed: {total_events}
Compliant: {compliant} ({compliant/total_events*100:.1f}% if total_events > 0 else 0)
Partial Compliance: {partial}
Non-Compliant: {non_compliant}
Overall Compliance Score: {compliance_score:.1f}%

The mission was conducted aboard {mission_log.vessel_name} from {mission_log.start_time} to {mission_log.end_time or 'ongoing'}.
"""

        # Generate lessons learned
        lessons_learned = []
        if non_compliant > 0:
            lessons_learned.append(
                f"{non_compliant} events did not meet doctrine requirements - ensure proper documentation procedures are followed"
            )
        if partial > 0:
            lessons_learned.append(
                f"{partial} events had partial compliance - review checklist for complete event logging"
            )
        if compliant == total_events:
            lessons_learned.append(
                "All events properly documented according to doctrine - excellent adherence to procedures"
            )

        # Generate recommendations
        recommendations = []
        if non_compliant > 0 or partial > 0:
            recommendations.append("Conduct refresher training on event documentation requirements")
            recommendations.append("Implement pre-mission checklist review of documentation procedures")

        recommendations.append("Continue post-mission debriefs to reinforce lessons learned")

        return {
            "summary": summary,
            "lessons_learned": lessons_learned,
            "recommendations": recommendations
        }

    def analyze_mission(self, mission_log: MissionLog) -> MissionAnalysis:
        """Analyze a complete mission log"""
        print(f"\n{'='*60}")
        print(f"Analyzing Mission: {mission_log.mission_name}")
        print(f"{'='*60}\n")

        # Run the graph
        initial_state = {
            "mission_log": mission_log,
            "current_event": None,
            "doctrine_context": [],
            "comparison_results": [],
            "summary": "",
            "lessons_learned": [],
            "recommendations": []
        }

        result = self.graph.invoke(initial_state)

        # Calculate compliance score
        comparisons = result["comparison_results"]
        if comparisons:
            compliant_count = sum(1 for c in comparisons if c.compliance_status == "compliant")
            overall_score = (compliant_count / len(comparisons)) * 100
        else:
            overall_score = 0.0

        # Create analysis object
        analysis = MissionAnalysis(
            mission_id=mission_log.mission_id,
            mission_name=mission_log.mission_name,
            comparisons=result["comparison_results"],
            summary=result["summary"],
            lessons_learned=result["lessons_learned"],
            recommendations=result["recommendations"],
            overall_compliance_score=overall_score
        )

        return analysis


if __name__ == "__main__":
    # Test the pipeline
    from mission_parser import MissionLogParser

    # Create sample mission log
    sample_data = MissionLogParser.generate_sample_mission_log()
    mission = MissionLogParser.parse_json_data(sample_data)

    # Analyze mission
    rag = MissionAnalysisRAG(use_local_llm=True)
    analysis = rag.analyze_mission(mission)

    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    print(analysis.summary)
    print("\nLessons Learned:")
    for lesson in analysis.lessons_learned:
        print(f"  - {lesson}")
    print("\nRecommendations:")
    for rec in analysis.recommendations:
        print(f"  - {rec}")
