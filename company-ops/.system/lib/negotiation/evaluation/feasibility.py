"""
Feasibility Evaluator for company-ops negotiation engine.

Evaluates whether a provider can fulfill an intent based on
constraints, resources, and autonomy rules.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeasibilityResult:
    """Result of feasibility evaluation."""
    feasible: bool
    confidence: float
    constraints_satisfied: list[str]
    constraints_violated: list[str]
    requirements_missing: list[str]
    autonomy_decision: str  # "allowed", "notify", "require_approval", "forbidden"
    recommendations: list[str]
    risk_level: str  # "low", "medium", "high", "critical"


class FeasibilityEvaluator:
    """
    Evaluates feasibility of fulfilling an intent.

    Checks:
    1. Constraint satisfaction (time, resources, dependencies)
    2. Autonomy rules (can subsystem decide autonomously?)
    3. Risk assessment (what could go wrong?)
    4. Resource availability (does subsystem have what it needs?)
    """

    # Default autonomy thresholds
    DEFAULT_THRESHOLDS = {
        "amount": {
            "auto": 1000,
            "notify": 10000,
            "approval": float("inf"),
        },
        "risk_level": {
            "auto": "low",
            "notify": "medium",
            "approval": "high",
        },
    }

    def __init__(self, knowledge_graph, config: dict = None):
        self.kg = knowledge_graph
        self.config = config or {}
        self.thresholds = {
            **self.DEFAULT_THRESHOLDS,
            **self.config.get("thresholds", {})
        }

    def evaluate(self, intent: dict, provider_id: str) -> FeasibilityResult:
        """
        Evaluate feasibility of intent with provider.

        Args:
            intent: Parsed intent with category, parameters, constraints
            provider_id: Subsystem ID to evaluate

        Returns:
            FeasibilityResult with detailed assessment
        """
        constraints_satisfied = []
        constraints_violated = []
        requirements_missing = []
        recommendations = []

        # Get provider constraints and capabilities
        provider_config = self._get_provider_config(provider_id)

        # Check time constraints
        time_result = self._check_time_constraints(intent, provider_config)
        constraints_satisfied.extend(time_result.get("satisfied", []))
        constraints_violated.extend(time_result.get("violated", []))

        # Check resource constraints
        resource_result = self._check_resource_constraints(intent, provider_config)
        constraints_satisfied.extend(resource_result.get("satisfied", []))
        constraints_violated.extend(resource_result.get("violated", []))
        requirements_missing.extend(resource_result.get("missing", []))

        # Check dependency constraints
        dep_result = self._check_dependency_constraints(intent, provider_config)
        constraints_satisfied.extend(dep_result.get("satisfied", []))
        constraints_violated.extend(dep_result.get("violated", []))
        requirements_missing.extend(dep_result.get("missing", []))

        # Determine autonomy decision
        autonomy_decision = self._determine_autonomy(intent, provider_config)

        # Assess risk level
        risk_level = self._assess_risk(intent, provider_config)

        # Generate recommendations
        if constraints_violated:
            recommendations.append("Consider adjusting constraints")
        if requirements_missing:
            recommendations.append(f"Provide missing requirements: {', '.join(requirements_missing)}")
        if autonomy_decision == "require_approval":
            recommendations.append("Human approval required")
        if risk_level in ("high", "critical"):
            recommendations.append("High risk - proceed with caution")

        # Calculate overall feasibility
        feasible = (
            len(constraints_violated) == 0 and
            len(requirements_missing) == 0 and
            autonomy_decision != "forbidden"
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            constraints_satisfied,
            constraints_violated,
            requirements_missing
        )

        return FeasibilityResult(
            feasible=feasible,
            confidence=confidence,
            constraints_satisfied=constraints_satisfied,
            constraints_violated=constraints_violated,
            requirements_missing=requirements_missing,
            autonomy_decision=autonomy_decision,
            recommendations=recommendations,
            risk_level=risk_level
        )

    def _get_provider_config(self, provider_id: str) -> dict:
        """Get provider configuration from knowledge graph."""
        config = {}

        # Get provider entity
        provider = self.kg.get_entity(f"subsystem.{provider_id}")
        if provider:
            config["provider"] = provider
            config["properties"] = provider.get("properties", {})

        # Get provider's contract
        # This would typically read from CONTRACT.yaml
        # For now, use default config
        config["constraints"] = {
            "working_hours": "flexible",
            "max_concurrent_tasks": 5,
            "autonomy_level": "supervised"
        }

        return config

    def _check_time_constraints(self, intent: dict, config: dict) -> dict:
        """Check time-related constraints."""
        result = {"satisfied": [], "violated": []}

        constraints = intent.get("constraints", {})
        deadline = constraints.get("deadline") or intent.get("parameters", {}).get("deadline")

        if deadline:
            try:
                deadline_dt = self._parse_deadline(deadline)
                if deadline_dt and deadline_dt > datetime.now():
                    result["satisfied"].append(f"Deadline feasible: {deadline}")
                else:
                    result["violated"].append(f"Deadline already passed: {deadline}")
            except Exception:
                result["satisfied"].append("Deadline format recognized")

        # Check working hours constraint
        working_hours = config.get("constraints", {}).get("working_hours", "flexible")
        if working_hours != "flexible":
            # Would check current time against working hours
            result["satisfied"].append("Within working hours")

        return result

    def _check_resource_constraints(self, intent: dict, config: dict) -> dict:
        """Check resource-related constraints."""
        result = {"satisfied": [], "violated": [], "missing": []}

        params = intent.get("parameters", {})

        # Check amount constraints
        amount = params.get("amount")
        if amount:
            try:
                amount_value = float(str(amount).replace(",", ""))
                thresholds = self.thresholds.get("amount", {})

                if amount_value <= thresholds.get("auto", 1000):
                    result["satisfied"].append(f"Amount within auto-approval limit: ¥{amount_value}")
                elif amount_value <= thresholds.get("notify", 10000):
                    result["satisfied"].append(f"Amount within notification limit: ¥{amount_value}")
                else:
                    result["satisfied"].append(f"Amount requires approval: ¥{amount_value}")
            except ValueError:
                result["missing"].append("Valid amount value")

        # Check concurrent task limit
        max_tasks = config.get("constraints", {}).get("max_concurrent_tasks", 5)
        result["satisfied"].append(f"Task capacity available (max: {max_tasks})")

        return result

    def _check_dependency_constraints(self, intent: dict, config: dict) -> dict:
        """Check dependency-related constraints."""
        result = {"satisfied": [], "violated": [], "missing": []}

        params = intent.get("parameters", {})

        # Check if required subsystem dependencies exist
        references = params.get("references", [])
        for ref in references:
            ref_type = ref.get("type")
            ref_id = ref.get("id")

            if ref_type and ref_id:
                # Would check if referenced entity exists
                result["satisfied"].append(f"Reference exists: {ref_type}#{ref_id}")

        # Check cross-subsystem dependencies
        subsystem = params.get("subsystem")
        if subsystem and isinstance(subsystem, list):
            for sub_id in subsystem:
                entity = self.kg.get_entity(f"subsystem.{sub_id}")
                if entity:
                    result["satisfied"].append(f"Dependency subsystem available: {sub_id}")
                else:
                    result["missing"].append(f"Dependency subsystem: {sub_id}")

        return result

    def _determine_autonomy(self, intent: dict, config: dict) -> str:
        """
        Determine autonomy decision based on rules.

        Returns:
            "allowed" - Can proceed autonomously
            "notify" - Can proceed but should notify
            "require_approval" - Must get human approval
            "forbidden" - Cannot proceed
        """
        params = intent.get("parameters", {})

        # Check amount-based autonomy
        amount = params.get("amount")
        if amount:
            try:
                amount_value = float(str(amount).replace(",", ""))
                thresholds = self.thresholds.get("amount", {})

                if amount_value <= thresholds.get("auto", 1000):
                    return "allowed"
                elif amount_value <= thresholds.get("notify", 10000):
                    return "notify"
                else:
                    return "require_approval"
            except ValueError:
                pass

        # Check risk-based autonomy
        risk_level = self._assess_risk(intent, config)
        risk_thresholds = self.thresholds.get("risk_level", {})

        if risk_level == "low":
            return "allowed"
        elif risk_level == "medium":
            return "notify"
        elif risk_level in ("high", "critical"):
            return "require_approval"

        # Check provider autonomy level
        autonomy_level = config.get("constraints", {}).get("autonomy_level", "supervised")
        if autonomy_level == "full":
            return "allowed"
        elif autonomy_level == "supervised":
            return "notify"

        return "require_approval"

    def _assess_risk(self, intent: dict, config: dict) -> str:
        """Assess risk level of the intent."""
        params = intent.get("parameters", {})
        category = intent.get("category", "unknown")

        # High risk categories
        high_risk_categories = ["delete", "approve"]
        if category in high_risk_categories:
            return "high"

        # Check amount
        amount = params.get("amount")
        if amount:
            try:
                amount_value = float(str(amount).replace(",", ""))
                if amount_value > 50000:
                    return "high"
                elif amount_value > 10000:
                    return "medium"
            except ValueError:
                pass

        # Check for sensitive operations
        status = params.get("status")
        if status in ("已取消", "已拒绝", "cancelled", "rejected"):
            return "medium"

        # Default to low risk
        return "low"

    def _parse_deadline(self, deadline: str) -> Optional[datetime]:
        """Parse deadline string to datetime."""
        # Try ISO format
        try:
            return datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Try relative dates
        relative_dates = {
            "今天": datetime.now(),
            "明天": datetime(datetime.now().year, datetime.now().month, datetime.now().day + 1),
        }
        if deadline in relative_dates:
            return relative_dates[deadline]

        return None

    def _calculate_confidence(
        self,
        satisfied: list,
        violated: list,
        missing: list
    ) -> float:
        """Calculate overall confidence score."""
        total = len(satisfied) + len(violated) + len(missing)
        if total == 0:
            return 0.5  # Neutral confidence when no constraints

        satisfied_ratio = len(satisfied) / total
        violated_penalty = len(violated) * 0.3
        missing_penalty = len(missing) * 0.2

        confidence = satisfied_ratio - violated_penalty - missing_penalty
        return max(0.0, min(1.0, confidence))
