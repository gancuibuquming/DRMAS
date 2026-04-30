import argparse
import asyncio

from app.research.checkpoint import CheckpointStore
from app.research.graph import ResearchGraph
from app.research.state import ResearchState


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Run DeepResearch multi-agent workflow")
    parser.add_argument("topic", help="Research topic or question")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard")
    parser.add_argument("--language", choices=["zh", "en"], default="zh")
    args = parser.parse_args()

    state = ResearchState(topic=args.topic, depth=args.depth, language=args.language)
    graph = ResearchGraph(CheckpointStore())

    print(f"Session: {state.session_id}\n")
    async for event in graph.run(state):
        prefix = f"[{event.type}]"
        if event.agent:
            prefix += f"[{event.agent}]"
        print(prefix, event.message)

    if state.final_report:
        print("\n" + "=" * 80)
        print(state.final_report)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
