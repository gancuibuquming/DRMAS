import json
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.research.state import ResearchState


class CheckpointStore:
    """Simple JSON checkpoint store.

    In production you can replace this with Redis/Postgres/S3.
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or get_settings().checkpoint_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def save(self, state: ResearchState) -> None:
        state.touch()
        path = self.path_for(state.session_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def load(self, session_id: str) -> ResearchState:
        path = self.path_for(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {session_id}")
        return ResearchState.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def exists(self, session_id: str) -> bool:
        return self.path_for(session_id).exists()
