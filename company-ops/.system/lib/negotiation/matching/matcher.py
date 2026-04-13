"""
Service Matcher for company-ops negotiation engine.

Matches intents to capable subsystems and their services.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ServiceMatch:
    """Represents a matched service."""
    subsystem_id: str
    service_id: str
    service_name: str
    capability_id: str
    match_score: float
    match_reasons: list[str]
    autonomy_level: str
    estimated_response_time: str


class ServiceMatcher:
    """
    Matches intents to subsystems that can handle them.

    Uses knowledge graph to find:
    1. Subsystems with matching capabilities
    2. Services that implement those capabilities
    3. Service metadata for autonomy and SLA
    """

    # Default capability to service type mappings
    CAPABILITY_SERVICE_MAP = {
        # 财务
        "账务处理": ["账户余额查询", "交易记录查询"],
        "财务报告": ["财务报告生成"],
        "预算管理": ["预算状态查询"],
        "费用审核": ["费用报销审核"],
        "税务处理": ["税务计算"],
        "现金流管理": ["预警通知"],

        # 法务
        "合同审核": ["合同审核"],
        "合规检查": ["合规检查"],
        "知识产权管理": ["知识产权查询"],
        "风险评估": ["风险评估"],
        "法律咨询": ["法律咨询"],
        "合同管理": ["合同查询", "合同到期提醒"],

        # Generic mappings
        "query": ["查询", "搜索", "获取"],
        "execute": ["执行", "处理", "完成"],
        "create": ["创建", "新建", "添加"],
        "update": ["更新", "修改", "编辑"],
        "delete": ["删除", "移除"],
        "approve": ["审批", "审核", "批准"],
        "report": ["报告", "报表", "统计"],
    }

    def __init__(self, knowledge_graph, config: dict = None):
        self.kg = knowledge_graph
        self.config = config or {}
        self.mappings = dict(self.CAPABILITY_SERVICE_MAP)

        # Load custom mappings
        if "custom_mappings" in self.config:
            self.mappings.update(self.config["custom_mappings"])

    def find_providers(self, intent: dict) -> list[ServiceMatch]:
        """
        Find subsystems that can handle an intent.

        Args:
            intent: Parsed intent with category, entities, parameters

        Returns:
            List of ServiceMatch sorted by match score
        """
        matches = []

        # Get intent category and extracted entities
        category = intent.get("category", "unknown")
        subcategory = intent.get("subcategory")
        entities = intent.get("entities", [])
        parameters = intent.get("parameters", {})

        # Extract subsystem hints from entities
        target_subsystem = parameters.get("subsystem")
        if isinstance(target_subsystem, list):
            target_subsystem = target_subsystem[0] if target_subsystem else None

        # Extract capability hints
        target_capability = parameters.get("capability")
        if isinstance(target_capability, list):
            target_capability = target_capability[0] if target_capability else None

        # Query knowledge graph for subsystems
        subsystems = self._get_all_subsystems()

        for subsystem in subsystems:
            subsystem_id = subsystem.get("id")
            if not subsystem_id:
                continue

            # If target subsystem specified, only match that
            if target_subsystem and subsystem_id != target_subsystem:
                continue

            # Get subsystem capabilities and services
            capabilities = self.get_subsystem_capabilities(subsystem_id)
            services = self.get_subsystem_services(subsystem_id)

            # Score matches
            for service in services:
                match_score = 0
                match_reasons = []

                service_name = service.get("name", "")
                service_capability = service.get("capability")

                # Check capability match
                if target_capability:
                    if self._capability_matches(service_capability, target_capability):
                        match_score += 0.5
                        match_reasons.append(f"能力匹配: {target_capability}")

                # Check service name match with intent keywords
                for entity in entities:
                    if entity.get("type") in ("capability", "subsystem"):
                        if self._text_matches(service_name, entity.get("value", "")):
                            match_score += 0.3
                            match_reasons.append(f"服务名匹配: {entity.get('value')}")

                # Check category-based matching
                category_services = self.mappings.get(category, [])
                for cs in category_services:
                    if cs in service_name:
                        match_score += 0.2
                        match_reasons.append(f"类别匹配: {category}")
                        break

                # Check subcategory match
                if subcategory:
                    subcategory_services = self.mappings.get(subcategory, [])
                    for ss in subcategory_services:
                        if ss in service_name:
                            match_score += 0.1
                            match_reasons.append(f"子类别匹配: {subcategory}")
                            break

                if match_score > 0:
                    match = ServiceMatch(
                        subsystem_id=subsystem_id,
                        service_id=service.get("service_id", ""),
                        service_name=service_name,
                        capability_id=service_capability or "",
                        match_score=min(1.0, match_score),
                        match_reasons=match_reasons,
                        autonomy_level=service.get("autonomy", "unknown"),
                        estimated_response_time=service.get("sla_response_time", "unknown")
                    )
                    matches.append(match)

        # Sort by match score
        matches.sort(key=lambda m: m.match_score, reverse=True)

        return matches

    def get_subsystem_capabilities(self, subsystem_id: str) -> list[dict]:
        """Get capabilities for a subsystem from local graph."""
        capabilities = []

        # Query local graph
        local_graph = self._get_local_graph(subsystem_id)
        if local_graph:
            for entity in local_graph.get("entities", []):
                if entity.get("type") == "capability":
                    capabilities.append(entity)

        return capabilities

    def get_subsystem_services(self, subsystem_id: str) -> list[dict]:
        """Get services for a subsystem from local graph."""
        services = []

        # Query local graph
        local_graph = self._get_local_graph(subsystem_id)
        if local_graph:
            for entity in local_graph.get("entities", []):
                if entity.get("type") == "service":
                    props = entity.get("properties", {})
                    services.append({
                        "service_id": props.get("service_id", entity.get("id")),
                        "name": entity.get("name", ""),
                        "capability": props.get("capability"),
                        "autonomy": props.get("autonomy", "unknown"),
                        "sla_response_time": props.get("sla_response_time", "unknown"),
                    })

        return services

    def find_service_by_name(
        self,
        subsystem_id: str,
        service_name: str
    ) -> Optional[dict]:
        """Find a specific service by name."""
        services = self.get_subsystem_services(subsystem_id)
        for service in services:
            if service_name in service.get("name", ""):
                return service
        return None

    def register_mapping(self, mapping: dict):
        """Register a new capability-service mapping."""
        for capability, services in mapping.items():
            if capability not in self.mappings:
                self.mappings[capability] = []
            self.mappings[capability].extend(services)

    def _get_all_subsystems(self) -> list[dict]:
        """Get all registered subsystems."""
        subsystems = []

        # Query global graph
        global_graph = self.kg.query.get_entity("company")
        if global_graph:
            # Get related subsystems
            related = self.kg.query.get_related_entities(
                "company",
                direction="outgoing",
                relation_type="owns"
            )
            for item in related:
                entity = item.get("entity", {})
                if entity.get("type") == "subsystem":
                    subsystems.append(entity)

        return subsystems

    def _get_local_graph(self, subsystem_id: str) -> Optional[dict]:
        """Get local graph for a subsystem."""
        try:
            return self.kg.load_subsystem_graph(subsystem_id)
        except Exception:
            return None

    def _capability_matches(self, service_cap: str, target_cap: str) -> bool:
        """Check if service capability matches target."""
        if not service_cap or not target_cap:
            return False

        # Normalize for comparison
        service_cap_lower = service_cap.lower().replace("_", "").replace("-", "")
        target_cap_lower = target_cap.lower().replace("_", "").replace("-", "")

        return (service_cap_lower == target_cap_lower or
                target_cap_lower in service_cap_lower or
                service_cap_lower in target_cap_lower)

    def _text_matches(self, text1: str, text2: str) -> bool:
        """Check if two texts match (fuzzy)."""
        if not text1 or not text2:
            return False

        t1_lower = text1.lower()
        t2_lower = text2.lower()

        return t2_lower in t1_lower or t1_lower in t2_lower
