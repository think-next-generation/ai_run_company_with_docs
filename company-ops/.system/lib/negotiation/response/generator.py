"""
Response Generator for company-ops negotiation engine.

Generates structured responses based on negotiation results.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NegotiationResponse:
    """Represents a negotiation response."""
    status: str  # "accepted", "rejected", "needs_info", "needs_approval", "negotiating"
    message: str
    actions: list[dict]
    next_steps: list[str]
    requires_human: bool
    estimated_completion: Optional[str]
    metadata: dict


class ResponseGenerator:
    """
    Generates responses for negotiation outcomes.

    Creates human-readable messages and structured action plans
    based on feasibility results and autonomy decisions.
    """

    # Status templates
    STATUS_TEMPLATES = {
        "accepted": {
            "zh": "请求已接受，正在处理中",
            "en": "Request accepted, processing"
        },
        "rejected": {
            "zh": "请求被拒绝",
            "en": "Request rejected"
        },
        "needs_info": {
            "zh": "需要更多信息才能处理请求",
            "en": "More information needed"
        },
        "needs_approval": {
            "zh": "请求需要人工审批",
            "en": "Request requires human approval"
        },
        "negotiating": {
            "zh": "正在与其他子系统协商",
            "en": "Negotiating with other subsystems"
        },
        "deferred": {
            "zh": "请求已推迟",
            "en": "Request deferred"
        },
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.language = self.config.get("language", "zh")

    def generate(
        self,
        intent: dict,
        match_result,
        feasibility_result
    ) -> NegotiationResponse:
        """
        Generate a negotiation response.

        Args:
            intent: Original intent
            match_result: ServiceMatch from matcher
            feasibility_result: FeasibilityResult from evaluator

        Returns:
            NegotiationResponse with status, message, and actions
        """
        # Determine status based on feasibility
        if not feasibility_result.feasible:
            status = self._determine_failure_status(feasibility_result)
        else:
            status = self._determine_success_status(feasibility_result)

        # Generate message
        message = self._generate_message(
            status,
            intent,
            match_result,
            feasibility_result
        )

        # Generate actions
        actions = self._generate_actions(
            status,
            intent,
            match_result,
            feasibility_result
        )

        # Generate next steps
        next_steps = self._generate_next_steps(
            status,
            feasibility_result
        )

        # Determine if human involvement needed
        requires_human = feasibility_result.autonomy_decision in (
            "require_approval",
            "forbidden"
        )

        # Estimate completion time
        estimated_completion = self._estimate_completion(
            status,
            match_result,
            feasibility_result
        )

        return NegotiationResponse(
            status=status,
            message=message,
            actions=actions,
            next_steps=next_steps,
            requires_human=requires_human,
            estimated_completion=estimated_completion,
            metadata={
                "intent_category": intent.get("category"),
                "provider": match_result.subsystem_id if match_result else None,
                "service": match_result.service_name if match_result else None,
                "autonomy_decision": feasibility_result.autonomy_decision,
                "risk_level": feasibility_result.risk_level,
                "confidence": feasibility_result.confidence,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _determine_failure_status(self, feasibility) -> str:
        """Determine status for infeasible requests."""
        if feasibility.requirements_missing:
            return "needs_info"
        elif feasibility.autonomy_decision == "forbidden":
            return "rejected"
        elif feasibility.constraints_violated:
            return "rejected"
        else:
            return "needs_info"

    def _determine_success_status(self, feasibility) -> str:
        """Determine status for feasible requests."""
        if feasibility.autonomy_decision == "require_approval":
            return "needs_approval"
        elif feasibility.autonomy_decision == "notify":
            return "accepted"  # Accepted with notification
        else:
            return "accepted"

    def _generate_message(
        self,
        status: str,
        intent: dict,
        match,
        feasibility
    ) -> str:
        """Generate human-readable message."""
        template = self.STATUS_TEMPLATES.get(status, {})
        base_message = template.get(self.language, template.get("en", ""))

        parts = [base_message]

        # Add provider info
        if match:
            provider_msg = {
                "zh": f"由 {match.subsystem_id} 处理",
                "en": f"Handled by {match.subsystem_id}"
            }
            parts.append(provider_msg.get(self.language, provider_msg["en"]))

        # Add reason for non-accepted status
        if status == "needs_info":
            if feasibility.requirements_missing:
                missing_msg = {
                    "zh": f"缺少: {', '.join(feasibility.requirements_missing)}",
                    "en": f"Missing: {', '.join(feasibility.requirements_missing)}"
                }
                parts.append(missing_msg.get(self.language, missing_msg["en"]))

        elif status == "rejected":
            if feasibility.constraints_violated:
                violated_msg = {
                    "zh": f"原因: {', '.join(feasibility.constraints_violated)}",
                    "en": f"Reason: {', '.join(feasibility.constraints_violated)}"
                }
                parts.append(violated_msg.get(self.language, violated_msg["en"]))

        elif status == "needs_approval":
            approval_msg = {
                "zh": f"风险等级: {feasibility.risk_level}，需要人工审批",
                "en": f"Risk level: {feasibility.risk_level}, requires human approval"
            }
            parts.append(approval_msg.get(self.language, approval_msg["en"]))

        return "。".join(parts) if self.language == "zh" else ". ".join(parts)

    def _generate_actions(
        self,
        status: str,
        intent: dict,
        match,
        feasibility
    ) -> list[dict]:
        """Generate action items based on status."""
        actions = []

        if status == "accepted":
            # Action to execute the service
            actions.append({
                "type": "execute_service",
                "provider": match.subsystem_id if match else None,
                "service": match.service_id if match else None,
                "parameters": intent.get("parameters", {}),
                "autonomy": feasibility.autonomy_decision
            })

            # Notification action if needed
            if feasibility.autonomy_decision == "notify":
                actions.append({
                    "type": "notify",
                    "channel": "human",
                    "message": f"Service execution started: {match.service_name if match else 'unknown'}"
                })

        elif status == "needs_info":
            # Action to request information
            actions.append({
                "type": "request_info",
                "required": feasibility.requirements_missing,
                "optional": feasibility.recommendations
            })

        elif status == "needs_approval":
            # Action to create approval request
            actions.append({
                "type": "request_approval",
                "risk_level": feasibility.risk_level,
                "justification": feasibility.recommendations,
                "timeout_hours": 24
            })

        elif status == "rejected":
            # Action to log rejection
            actions.append({
                "type": "log_rejection",
                "reason": feasibility.constraints_violated,
                "intent": intent.get("raw_text", "")
            })

        return actions

    def _generate_next_steps(
        self,
        status: str,
        feasibility
    ) -> list[str]:
        """Generate next steps for the user."""
        steps = []

        if status == "accepted":
            steps_msg = {
                "zh": "等待执行完成",
                "en": "Wait for execution to complete"
            }
            steps.append(steps_msg.get(self.language, steps_msg["en"]))

            if feasibility.recommendations:
                steps.extend(feasibility.recommendations)

        elif status == "needs_info":
            steps_msg = {
                "zh": "提供所需信息后重新提交",
                "en": "Resubmit with required information"
            }
            steps.append(steps_msg.get(self.language, steps_msg["en"]))

        elif status == "needs_approval":
            steps_msg = {
                "zh": "等待人工审批",
                "en": "Wait for human approval"
            }
            steps.append(steps_msg.get(self.language, steps_msg["en"]))

            check_msg = {
                "zh": "检查 human/reviews/ 目录",
                "en": "Check human/reviews/ directory"
            }
            steps.append(check_msg.get(self.language, check_msg["en"]))

        elif status == "rejected":
            steps_msg = {
                "zh": "根据拒绝原因调整请求",
                "en": "Adjust request based on rejection reason"
            }
            steps.append(steps_msg.get(self.language, steps_msg["en"]))

        return steps

    def _estimate_completion(
        self,
        status: str,
        match,
        feasibility
    ) -> Optional[str]:
        """Estimate completion time."""
        if status != "accepted":
            return None

        if match and match.estimated_response_time:
            return match.estimated_response_time

        # Default estimates based on autonomy
        if feasibility.autonomy_decision == "allowed":
            return "< 1 hour"
        elif feasibility.autonomy_decision == "notify":
            return "< 4 hours"
        else:
            return "< 24 hours"

    def format_response(self, response: NegotiationResponse) -> str:
        """Format response as readable text."""
        lines = [
            f"Status: {response.status}",
            f"Message: {response.message}",
        ]

        if response.actions:
            lines.append("Actions:")
            for i, action in enumerate(response.actions, 1):
                lines.append(f"  {i}. {action.get('type', 'unknown')}: {action}")

        if response.next_steps:
            lines.append("Next Steps:")
            for step in response.next_steps:
                lines.append(f"  - {step}")

        if response.estimated_completion:
            lines.append(f"Estimated Completion: {response.estimated_completion}")

        return "\n".join(lines)
