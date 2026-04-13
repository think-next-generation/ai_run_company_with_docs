"""
Intent Extractor for company-ops negotiation engine.

Extracts structured entities and parameters from natural language intents.
"""

import re
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractedEntity:
    """Represents an extracted entity."""
    type: str
    value: str
    raw_text: str
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedIntent:
    """Represents a fully extracted intent."""
    raw_text: str
    entities: list[ExtractedEntity]
    parameters: dict
    constraints: dict
    confidence: float


class IntentExtractor:
    """
    Extracts entities and parameters from intent text.

    Supports extraction of:
    - Subsystem references (财务, 法务, products/xxx)
    - Capability references (账务处理, 合同审核)
    - Time expressions (明天, 下周, 2024-04-01)
    - Amount expressions (1000元, ¥5000)
    - Status values (待审核, 已完成)
    - Document references (合同#123, 报告-2024Q1)
    """

    # Entity patterns
    PATTERNS = {
        "subsystem": [
            r"(财务|法务|人事|行政|技术|产品|运营|市场|销售)",
            r"subsystems/([a-zA-Z0-9_-]+)",
            r"products/([a-zA-Z0-9_-]+)",
        ],
        "capability": [
            r"(账务处理|财务报告|预算管理|费用审核|税务处理)",
            r"(合同审核|合规检查|知识产权|风险评估|法律咨询)",
            r"capability\.([a-zA-Z0-9_.]+)",
        ],
        "amount": [
            r"(\d+(?:\.\d{1,2})?)\s*[元¥]",
            r"[¥￥]\s*(\d+(?:\.\d{1,2})?)",
            r"(\d+(?:\.\d{1,2})?)\s*(?:万|千|百)",
        ],
        "date": [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{4}/\d{2}/\d{2})",
            r"(今天|明天|后天|昨天)",
            r"(本周|下周|上周)",
            r"(本月|下月|上月)",
            r"(\d+)月(\d+)[日号]",
        ],
        "time": [
            r"(\d{1,2}):(\d{2})",
            r"(上午|下午|早上|晚上)\s*(\d{1,2})[点时]",
            r"(\d{1,2})[点时](\d{1,2})?分?",
        ],
        "status": [
            r"(待审核|待处理|进行中|已完成|已取消|已拒绝)",
            r"(pending|in_progress|completed|cancelled|rejected)",
            r"(草稿|生效|过期|终止)",
        ],
        "reference": [
            r"[#＃]([A-Za-z0-9-]+)",
            r"(合同|报告|申请|工单)[#＃-]?([A-Za-z0-9-]+)",
        ],
        "priority": [
            r"(紧急|重要|一般|低优先级)",
            r"(urgent|high|normal|low)",
            r"[Pp](0|1|2|3)",
        ],
        "period": [
            r"(\d{4})[年-](Q[1-4]|第[一二三四]季度)",
            r"(\d{4})年?(\d{1,2})月?",
            r"(Q[1-4]|第[一二三四]季度)",
        ],
    }

    # Amount multipliers
    AMOUNT_MULTIPLIERS = {
        "万": 10000,
        "千": 1000,
        "百": 100,
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.patterns = dict(self.PATTERNS)

        # Load custom patterns
        if "custom_patterns" in self.config:
            for entity_type, patterns in self.config["custom_patterns"].items():
                if entity_type not in self.patterns:
                    self.patterns[entity_type] = []
                self.patterns[entity_type].extend(patterns)

    def extract(self, intent_text: str) -> dict:
        """
        Extract entities and parameters from intent text.

        Args:
            intent_text: Natural language intent description

        Returns:
            Dict with:
                - raw_text: Original text
                - entities: List of extracted entities
                - parameters: Structured parameters dict
                - constraints: Extracted constraints
                - confidence: Overall extraction confidence
        """
        entities = []
        parameters = {}
        constraints = {}

        # Extract each entity type
        for entity_type, patterns in self.patterns.items():
            extracted = self._extract_type(intent_text, entity_type, patterns)
            entities.extend(extracted)

            # Build parameters from extracted entities
            if extracted:
                if entity_type in ("subsystem", "capability"):
                    parameters[entity_type] = [e.value for e in extracted]
                elif entity_type in ("amount", "date", "time", "status", "priority"):
                    parameters[entity_type] = extracted[0].value
                    if len(extracted) > 1:
                        parameters[f"{entity_type}_list"] = [e.value for e in extracted]
                elif entity_type == "reference":
                    parameters["references"] = [
                        {"type": e.metadata.get("ref_type"), "id": e.value}
                        for e in extracted
                    ]
                elif entity_type == "period":
                    parameters["period"] = extracted[0].value

        # Extract constraints (must/shoud/can patterns)
        constraints = self._extract_constraints(intent_text)

        # Calculate confidence
        confidence = self._calculate_confidence(entities, intent_text)

        return {
            "raw_text": intent_text,
            "entities": [
                {
                    "type": e.type,
                    "value": e.value,
                    "raw_text": e.raw_text,
                    "confidence": e.confidence,
                    "metadata": e.metadata
                }
                for e in entities
            ],
            "parameters": parameters,
            "constraints": constraints,
            "confidence": confidence
        }

    def _extract_type(
        self,
        text: str,
        entity_type: str,
        patterns: list[str]
    ) -> list[ExtractedEntity]:
        """Extract entities of a specific type."""
        extracted = []

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                raw_text = match.group(0)
                value = self._normalize_value(entity_type, match)

                if value:
                    entity = ExtractedEntity(
                        type=entity_type,
                        value=value,
                        raw_text=raw_text,
                        confidence=0.9 if match.start() == 0 else 0.7,
                        metadata=self._extract_metadata(entity_type, match)
                    )
                    extracted.append(entity)

        return extracted

    def _normalize_value(self, entity_type: str, match) -> Optional[str]:
        """Normalize extracted value."""
        groups = match.groups()

        if entity_type == "amount":
            # Extract numeric value
            amount_str = groups[0] if groups else None
            if amount_str:
                try:
                    amount = float(amount_str)
                    # Check for multipliers in full text
                    full_text = match.group(0)
                    for suffix, mult in self.AMOUNT_MULTIPLIERS.items():
                        if suffix in full_text:
                            amount *= mult
                            break
                    return str(amount)
                except ValueError:
                    return None

        elif entity_type == "date":
            if groups[0] in ("今天", "明天", "后天", "昨天"):
                return self._relative_date(groups[0])
            elif groups[0] in ("本周", "下周", "上周"):
                return groups[0]
            elif re.match(r"\d{4}-\d{2}-\d{2}", groups[0]):
                return groups[0]
            elif len(groups) >= 2 and groups[0].isdigit() and groups[1].isdigit():
                # X月X日 format
                year = datetime.now().year
                month, day = int(groups[0]), int(groups[1])
                return f"{year}-{month:02d}-{day:02d}"
            return groups[0]

        elif entity_type == "time":
            if len(groups) >= 2:
                hour = int(groups[-2])
                minute = int(groups[-1]) if groups[-1] else 0
                return f"{hour:02d}:{minute:02d}"
            return groups[0]

        elif entity_type == "period":
            if len(groups) >= 2:
                year = groups[0]
                quarter = groups[1]
                quarter_num = {
                    "Q1": "01", "Q2": "04", "Q3": "07", "Q4": "10",
                    "第一季度": "Q1", "第二季度": "Q2", "第三季度": "Q3", "第四季度": "Q4",
                }.get(quarter, quarter)
                return f"{year}-{quarter_num}"
            return groups[0]

        elif entity_type == "reference":
            if len(groups) >= 2:
                return groups[-1]  # Return the ID part
            return groups[0]

        # Default: return first group or full match
        return groups[0] if groups else match.group(0)

    def _extract_metadata(self, entity_type: str, match) -> dict:
        """Extract additional metadata for an entity."""
        metadata = {}

        if entity_type == "reference":
            groups = match.groups()
            if len(groups) >= 2:
                metadata["ref_type"] = groups[0]  # e.g., "合同"
                metadata["ref_id"] = groups[1]    # e.g., "123"

        elif entity_type == "amount":
            full_text = match.group(0)
            if "万" in full_text:
                metadata["unit"] = "万"
            elif "千" in full_text:
                metadata["unit"] = "千"

        return metadata

    def _extract_constraints(self, text: str) -> dict:
        """Extract constraint expressions."""
        constraints = {}

        # Must/have to patterns
        must_patterns = [
            r"必须(.+)",
            r"一定要(.+)",
            r"需要(.+)",
            r"must (.+)",
            r"required to (.+)",
        ]
        for pattern in must_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                constraints["must"] = constraints.get("must", [])
                constraints["must"].append(match.group(1))

        # Should/prefer patterns
        should_patterns = [
            r"最好(.+)",
            r"建议(.+)",
            r"优先(.+)",
            r"should (.+)",
            r"prefer (.+)",
        ]
        for pattern in should_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                constraints["should"] = constraints.get("should", [])
                constraints["should"].append(match.group(1))

        # Deadline patterns
        deadline_patterns = [
            r"截止(.+)",
            r"在(.+)之前",
            r"before (.+)",
            r"by (.+)",
            r"deadline[:\s]+(.+)",
        ]
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                constraints["deadline"] = match.group(1)

        return constraints

    def _relative_date(self, text: str) -> str:
        """Convert relative date to ISO format."""
        from datetime import timedelta

        today = datetime.now().date()

        if text == "今天":
            return today.isoformat()
        elif text == "明天":
            return (today + timedelta(days=1)).isoformat()
        elif text == "后天":
            return (today + timedelta(days=2)).isoformat()
        elif text == "昨天":
            return (today - timedelta(days=1)).isoformat()

        return text

    def _calculate_confidence(
        self,
        entities: list[ExtractedEntity],
        text: str
    ) -> float:
        """Calculate overall extraction confidence."""
        if not entities:
            return 0.0

        # Base confidence from individual entities
        entity_confidence = sum(e.confidence for e in entities) / len(entities)

        # Adjust based on coverage
        text_words = len(text.split())
        covered_chars = sum(len(e.raw_text) for e in entities)
        coverage = covered_chars / max(len(text), 1)

        # Weighted combination
        confidence = 0.7 * entity_confidence + 0.3 * min(coverage * 2, 1.0)

        return round(min(1.0, confidence), 2)

    def register_pattern(self, entity_type: str, pattern: str):
        """Register a custom pattern for an entity type."""
        if entity_type not in self.patterns:
            self.patterns[entity_type] = []
        self.patterns[entity_type].append(pattern)
