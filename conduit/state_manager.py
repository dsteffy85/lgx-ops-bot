"""Conduit State Manager — tracks sync state per connection"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

STATE_DIR = Path.home() / ".conduit" / "state"
HISTORY_DIR = Path.home() / ".conduit" / "history"

class StateManager:
    def __init__(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    def get_state(self, name: str) -> Dict[str, Any]:
        f = STATE_DIR / f"{name}.json"
        return json.loads(f.read_text()) if f.exists() else {}

    def save_state(self, name: str, state: Dict[str, Any]):
        state["_updated_at"] = datetime.utcnow().isoformat()
        (STATE_DIR / f"{name}.json").write_text(json.dumps(state, indent=2, default=str))

    def record_run(self, name: str, result: Dict[str, Any]):
        result["_recorded_at"] = datetime.utcnow().isoformat()
        with open(HISTORY_DIR / f"{name}.jsonl", "a") as f:
            f.write(json.dumps(result, default=str) + "\n")

    def get_history(self, name: str, limit: int = 20) -> List[Dict]:
        f = HISTORY_DIR / f"{name}.jsonl"
        if not f.exists(): return []
        runs = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        return runs[-limit:]

    def get_all_statuses(self) -> Dict[str, Dict]:
        statuses = {}
        for f in STATE_DIR.glob("*.json"):
            state = json.loads(f.read_text())
            history = self.get_history(f.stem, 1)
            statuses[f.stem] = {
                "last_sync": state.get("_updated_at"),
                "last_status": history[-1].get("status") if history else "never_run",
            }
        return statuses
