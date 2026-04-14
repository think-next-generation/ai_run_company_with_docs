#!/usr/bin/env python3
"""Simple CLI for knowledge queries"""

import sys
import asyncio
from knowledge_engine import KnowledgeEngine


async def main():
    if len(sys.argv) < 2:
        print("Usage: python query_knowledge.py <question>")
        print("Example: python query_knowledge.py '财务 子系统目标'")
        sys.exit(1)
    
    question = sys.argv[1]
    engine = KnowledgeEngine()
    result = await engine.query(question)
    
    print("=" * 50)
    print("Answer:")
    print(result.answer)
    print("=" * 50)
    print("Sources:")
    print(f"  Organization Graph: {len(result.sources.get('organization', []))} results")
    print(f"  Wiki: {len(result.sources.get('wiki', []))} results")


if __name__ == "__main__":
    asyncio.run(main())
