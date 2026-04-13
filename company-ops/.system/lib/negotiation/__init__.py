"""
Negotiation Engine for company-ops.

Enables dynamic, intent-based interaction between subsystems
without fixed API contracts.
"""

from .intent.classifier import IntentClassifier
from .intent.extractor import IntentExtractor
from .matching.matcher import ServiceMatcher
from .evaluation.feasibility import FeasibilityEvaluator
from .response.generator import ResponseGenerator
from .orchestration.orchestrator import NegotiationOrchestrator

__version__ = "1.0.0"
__all__ = [
    "IntentClassifier",
    "IntentExtractor",
    "ServiceMatcher",
    "FeasibilityEvaluator",
    "ResponseGenerator",
    "NegotiationOrchestrator",
    "NegotiationEngine",
]


class NegotiationEngine:
    """
    Main interface for the negotiation engine.

    Orchestrates the full negotiation flow:
    1. Intent classification and extraction
    2. Service matching
    3. Feasibility evaluation
    4. Response generation
    """

    def __init__(self, knowledge_graph, config: dict = None):
        """
        Initialize the negotiation engine.

        Args:
            knowledge_graph: KnowledgeGraph instance
            config: Optional configuration
        """
        self.kg = knowledge_graph
        self.config = config or {}

        # Initialize components
        self.classifier = IntentClassifier(self.config.get("classifier", {}))
        self.extractor = IntentExtractor(self.config.get("extractor", {}))
        self.matcher = ServiceMatcher(knowledge_graph, self.config.get("matcher", {}))
        self.evaluator = FeasibilityEvaluator(knowledge_graph, self.config.get("evaluator", {}))
        self.generator = ResponseGenerator(self.config.get("generator", {}))
        self.orchestrator = NegotiationOrchestrator(
            self.classifier,
            self.extractor,
            self.matcher,
            self.evaluator,
            self.generator,
            self.config.get("orchestrator", {})
        )

    def process_request(self, request: dict) -> dict:
        """
        Process a negotiation request.

        Args:
            request: Request dict with:
                - intent: Natural language intent description
                - requestor: Requesting subsystem ID
                - payload: Optional additional data
                - deadline: Optional deadline
                - priority: Optional priority

        Returns:
            Response dict with negotiation result
        """
        return self.orchestrator.negotiate(request)

    def classify_intent(self, intent_text: str) -> dict:
        """Classify an intent text into categories."""
        return self.classifier.classify(intent_text)

    def extract_entities(self, intent_text: str) -> dict:
        """Extract entities from an intent text."""
        return self.extractor.extract(intent_text)

    def find_providers(self, intent: dict) -> list:
        """Find subsystems that can handle an intent."""
        return self.matcher.find_providers(intent)

    def evaluate_feasibility(self, intent: dict, provider: str) -> dict:
        """Evaluate if a provider can fulfill an intent."""
        return self.evaluator.evaluate(intent, provider)

    def get_capabilities(self, subsystem_id: str) -> list:
        """Get capabilities of a subsystem."""
        return self.matcher.get_subsystem_capabilities(subsystem_id)

    def register_intent_pattern(self, pattern: dict):
        """Register a new intent pattern for classification."""
        self.classifier.register_pattern(pattern)

    def register_service_mapping(self, mapping: dict):
        """Register a new service mapping for matching."""
        self.matcher.register_mapping(mapping)
