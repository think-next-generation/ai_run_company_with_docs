"""
Negotiation Orchestrator for company-ops negotiation engine.

Orchestrates the complete negotiation flow from intent to response.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class NegotiationContext:
    """Context for a negotiation session."""
    request_id: str
    requestor: str
    intent_text: str
    started_at: str
    status: str
    steps_completed: list[str]
    current_step: Optional[str]


class NegotiationOrchestrator:
    """
    Orchestrates the complete negotiation flow.

    Flow:
    1. Classify intent
    2. Extract entities
    3. Find matching providers
    4. Evaluate feasibility
    5. Generate response
    """

    def __init__(
        self,
        classifier,
        extractor,
        matcher,
        evaluator,
        generator,
        config: dict = None
    ):
        self.classifier = classifier
        self.extractor = extractor
        self.matcher = matcher
        self.evaluator = evaluator
        self.generator = generator
        self.config = config or {}

        # Active negotiations tracking
        self.active_negotiations: dict[str, NegotiationContext] = {}

    def negotiate(self, request: dict) -> dict:
        """
        Execute the full negotiation flow.

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
        # Generate request ID
        request_id = request.get("request_id") or str(uuid.uuid4())[:8]
        intent_text = request.get("intent", "")
        requestor = request.get("requestor", "unknown")

        # Initialize context
        context = NegotiationContext(
            request_id=request_id,
            requestor=requestor,
            intent_text=intent_text,
            started_at=datetime.now().isoformat(),
            status="processing",
            steps_completed=[],
            current_step="classify"
        )
        self.active_negotiations[request_id] = context

        try:
            # Step 1: Classify intent
            classification = self.classifier.classify(intent_text)
            context.steps_completed.append("classify")
            context.current_step = "extract"

            # Step 2: Extract entities
            extraction = self.extractor.extract(intent_text)
            context.steps_completed.append("extract")
            context.current_step = "match"

            # Combine into parsed intent
            parsed_intent = {
                "raw_text": intent_text,
                "category": classification.get("category"),
                "subcategory": classification.get("subcategory"),
                "classification_confidence": classification.get("confidence"),
                "entities": extraction.get("entities", []),
                "parameters": extraction.get("parameters", {}),
                "constraints": {**extraction.get("constraints", {}), **request.get("constraints", {})},
                "requestor": requestor,
                "deadline": request.get("deadline"),
                "priority": request.get("priority", "normal"),
            }

            # Step 3: Find matching providers
            matches = self.matcher.find_providers(parsed_intent)
            context.steps_completed.append("match")

            if not matches:
                # No providers found
                context.status = "no_provider"
                return self._create_no_provider_response(request_id, parsed_intent)

            # Use best match
            best_match = matches[0]
            context.current_step = "evaluate"

            # Step 4: Evaluate feasibility
            feasibility = self.evaluator.evaluate(parsed_intent, best_match.subsystem_id)
            context.steps_completed.append("evaluate")
            context.current_step = "respond"

            # Step 5: Generate response
            response = self.generator.generate(parsed_intent, best_match, feasibility)
            context.steps_completed.append("respond")
            context.status = response.status

            # Build final response
            return {
                "request_id": request_id,
                "status": response.status,
                "message": response.message,
                "provider": {
                    "subsystem_id": best_match.subsystem_id,
                    "service_id": best_match.service_id,
                    "service_name": best_match.service_name,
                },
                "actions": response.actions,
                "next_steps": response.next_steps,
                "requires_human": response.requires_human,
                "estimated_completion": response.estimated_completion,
                "metadata": {
                    **response.metadata,
                    "match_score": best_match.match_score,
                    "match_reasons": best_match.match_reasons,
                    "feasibility_confidence": feasibility.confidence,
                    "autonomy_decision": feasibility.autonomy_decision,
                    "risk_level": feasibility.risk_level,
                    "constraints_satisfied": feasibility.constraints_satisfied,
                    "constraints_violated": feasibility.constraints_violated,
                    "requirements_missing": feasibility.requirements_missing,
                },
                "negotiation_context": {
                    "request_id": request_id,
                    "started_at": context.started_at,
                    "completed_at": datetime.now().isoformat(),
                    "steps": context.steps_completed,
                }
            }

        except Exception as e:
            context.status = "error"
            return {
                "request_id": request_id,
                "status": "error",
                "message": f"Negotiation failed: {str(e)}",
                "provider": None,
                "actions": [],
                "next_steps": ["Retry the request", "Contact system administrator"],
                "requires_human": True,
                "error": str(e),
            }

    def _create_no_provider_response(self, request_id: str, intent: dict) -> dict:
        """Create response when no provider is found."""
        return {
            "request_id": request_id,
            "status": "no_provider",
            "message": f"No subsystem found that can handle: {intent.get('category', 'unknown')}",
            "provider": None,
            "actions": [
                {
                    "type": "log_no_provider",
                    "intent_category": intent.get("category"),
                    "intent_text": intent.get("raw_text", "")
                }
            ],
            "next_steps": [
                "Check if capability exists in any subsystem",
                "Consider creating a new subsystem for this capability",
                "Simplify the request"
            ],
            "requires_human": True,
            "metadata": {
                "intent_category": intent.get("category"),
                "intent_subcategory": intent.get("subcategory"),
            }
        }

    def get_negotiation_status(self, request_id: str) -> Optional[dict]:
        """Get status of an active negotiation."""
        context = self.active_negotiations.get(request_id)
        if not context:
            return None

        return {
            "request_id": context.request_id,
            "requestor": context.requestor,
            "intent": context.intent_text,
            "started_at": context.started_at,
            "status": context.status,
            "steps_completed": context.steps_completed,
            "current_step": context.current_step,
        }

    def cancel_negotiation(self, request_id: str) -> bool:
        """Cancel an active negotiation."""
        if request_id in self.active_negotiations:
            context = self.active_negotiations[request_id]
            context.status = "cancelled"
            return True
        return False

    def get_active_negotiations(self) -> list[dict]:
        """Get all active negotiations."""
        return [
            self.get_negotiation_status(rid)
            for rid in self.active_negotiations.keys()
            if self.active_negotiations[rid].status not in ("completed", "cancelled", "error")
        ]

    def cleanup_completed(self, max_age_hours: int = 24):
        """Clean up completed negotiations older than max_age_hours."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []

        for request_id, context in self.active_negotiations.items():
            if context.status in ("completed", "cancelled", "error"):
                started = datetime.fromisoformat(context.started_at)
                if started < cutoff:
                    to_remove.append(request_id)

        for request_id in to_remove:
            del self.active_negotiations[request_id]

        return len(to_remove)
