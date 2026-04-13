"""
Intent Classifier for company-ops negotiation engine.

Classifies natural language intents into structured categories.
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class IntentCategory:
    """Represents a classified intent category."""
    category: str
    subcategory: Optional[str]
    confidence: float
    keywords_matched: list[str]


class IntentClassifier:
    """
    Classifies intents into predefined categories.

    Categories are based on common business operations:
    - query: Information retrieval requests
    - execute: Action execution requests
    - create: Resource creation requests
    - update: Resource modification requests
    - delete: Resource deletion requests
    - approve: Approval/authorization requests
    - report: Report generation requests
    - coordinate: Cross-subsystem coordination
    """

    # Default intent patterns
    DEFAULT_PATTERNS = {
        "query": {
            "keywords": [
                "查询", "获取", "显示", "列出", "查看", "搜索", "找",
                "query", "get", "show", "list", "find", "search", "what", "which"
            ],
            "subcategories": {
                "status": ["状态", "进度", "情况", "status", "progress"],
                "balance": ["余额", "balance", "账户"],
                "history": ["历史", "记录", "history", "record", "log"],
                "detail": ["详情", "详细", "detail", "info", "information"],
            }
        },
        "execute": {
            "keywords": [
                "执行", "处理", "完成", "运行", "操作",
                "execute", "run", "process", "do", "perform", "handle"
            ],
            "subcategories": {
                "payment": ["付款", "支付", "转账", "pay", "payment", "transfer"],
                "approval": ["审批", "审核", "approve", "review", "audit"],
                "transfer": ["转移", "调拨", "transfer", "allocate"],
            }
        },
        "create": {
            "keywords": [
                "创建", "新建", "添加", "生成", "建立",
                "create", "new", "add", "generate", "make", "build"
            ],
            "subcategories": {
                "document": ["文档", "报告", "合同", "document", "report", "contract"],
                "record": ["记录", "条目", "record", "entry", "item"],
                "task": ["任务", "工单", "task", "ticket", "job"],
            }
        },
        "update": {
            "keywords": [
                "更新", "修改", "编辑", "变更", "调整",
                "update", "modify", "edit", "change", "adjust"
            ],
            "subcategories": {
                "status": ["状态", "status"],
                "config": ["配置", "设置", "config", "setting"],
                "content": ["内容", "content", "data"],
            }
        },
        "delete": {
            "keywords": [
                "删除", "移除", "取消", "作废",
                "delete", "remove", "cancel", "drop"
            ]
        },
        "approve": {
            "keywords": [
                "批准", "同意", "通过", "许可", "授权",
                "approve", "accept", "authorize", "permit", "grant"
            ],
            "subcategories": {
                "expense": ["报销", "费用", "expense", "reimburse"],
                "contract": ["合同", "contract"],
                "budget": ["预算", "budget"],
            }
        },
        "report": {
            "keywords": [
                "报告", "报表", "统计", "分析", "汇总",
                "report", "summary", "statistics", "analysis", "overview"
            ],
            "subcategories": {
                "financial": ["财务", "financ", "accounting"],
                "operation": ["运营", "operation", "business"],
                "compliance": ["合规", "compliance", "audit"],
            }
        },
        "coordinate": {
            "keywords": [
                "协调", "通知", "同步", "分配", "调度",
                "coordinate", "notify", "sync", "assign", "schedule"
            ]
        },
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.patterns = dict(self.DEFAULT_PATTERNS)

        # Load custom patterns from config
        if "custom_patterns" in self.config:
            for category, pattern in self.config["custom_patterns"].items():
                if category in self.patterns:
                    self.patterns[category]["keywords"].extend(pattern.get("keywords", []))
                    if "subcategories" in pattern:
                        if "subcategories" not in self.patterns[category]:
                            self.patterns[category]["subcategories"] = {}
                        self.patterns[category]["subcategories"].update(pattern["subcategories"])
                else:
                    self.patterns[category] = pattern

    def classify(self, intent_text: str) -> dict:
        """
        Classify an intent text.

        Args:
            intent_text: Natural language intent description

        Returns:
            Dict with:
                - category: Primary category
                - subcategory: Subcategory (if any)
                - confidence: Classification confidence (0-1)
                - keywords_matched: List of matched keywords
        """
        intent_lower = intent_text.lower()
        scores = {}

        for category, pattern in self.patterns.items():
            score = 0
            matched_keywords = []

            # Check main keywords
            for keyword in pattern.get("keywords", []):
                if keyword.lower() in intent_lower:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                scores[category] = {
                    "score": score,
                    "keywords": matched_keywords,
                    "subcategories": pattern.get("subcategories", {})
                }

        if not scores:
            return {
                "category": "unknown",
                "subcategory": None,
                "confidence": 0.0,
                "keywords_matched": []
            }

        # Find best category
        best_category = max(scores.keys(), key=lambda k: scores[k]["score"])
        best_score = scores[best_category]

        # Check subcategories
        subcategory = None
        sub_scores = {}
        for sub_name, sub_keywords in best_score.get("subcategories", {}).items():
            sub_score = sum(1 for kw in sub_keywords if kw.lower() in intent_lower)
            if sub_score > 0:
                sub_scores[sub_name] = sub_score

        if sub_scores:
            subcategory = max(sub_scores.keys(), key=lambda k: sub_scores[k])

        # Calculate confidence
        max_possible = len(best_score["keywords"]) + (
            len(best_score.get("subcategories", {}).get(subcategory, []))
            if subcategory else 0
        )
        confidence = min(1.0, best_score["score"] / max(1, max_possible / 2))

        return {
            "category": best_category,
            "subcategory": subcategory,
            "confidence": round(confidence, 2),
            "keywords_matched": best_score["keywords"]
        }

    def register_pattern(self, pattern: dict):
        """
        Register a new intent pattern.

        Args:
            pattern: Dict with category, keywords, and optional subcategories
        """
        category = pattern.get("category")
        if not category:
            return

        if category not in self.patterns:
            self.patterns[category] = {"keywords": [], "subcategories": {}}

        self.patterns[category]["keywords"].extend(pattern.get("keywords", []))

        if "subcategories" in pattern:
            if "subcategories" not in self.patterns[category]:
                self.patterns[category]["subcategories"] = {}
            self.patterns[category]["subcategories"].update(pattern["subcategories"])

    def get_categories(self) -> list[str]:
        """Get all known categories."""
        return list(self.patterns.keys())

    def get_pattern(self, category: str) -> Optional[dict]:
        """Get pattern for a specific category."""
        return self.patterns.get(category)
