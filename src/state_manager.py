import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class StateManager:
    def __init__(self, base_dir: str = "."):
        self.base_dir = os.path.abspath(base_dir)
        self.settings = self._load_json(os.path.join(self.base_dir, "config", "settings.json"))
        self.skills_catalog = self._load_json(os.path.join(self.base_dir, "skills", "catalog.json"))
        self.mcp_catalog = self._load_json(os.path.join(self.base_dir, "mcp", "catalog.json"))

        self.state_dir = self._resolve_path(self.settings.get("state_dir", "state"))
        self.checkpoints_dir = self._resolve_path(self.settings.get("checkpoints_dir", "state/checkpoints"))
        self.history_dir = self._resolve_path(self.settings.get("history_dir", "state/history"))

        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)

    def _resolve_path(self, rel_or_abs: str) -> str:
        if os.path.isabs(rel_or_abs):
            return rel_or_abs
        return os.path.normpath(os.path.join(self.base_dir, rel_or_abs))

    def _load_json(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required JSON file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_unity_target_config_path(self) -> str:
        unity_root = self.settings["unity_project_root"]
        rel_target = self.settings["target_terrain_config_relpath"]
        return os.path.normpath(os.path.join(unity_root, rel_target))

    def new_session_id(self) -> str:
        return datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")

    def save_checkpoint(self, session_id: str, stage_name: str, payload: Dict[str, Any]) -> str:
        session_dir = os.path.join(self.checkpoints_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)

        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "session_id": session_id,
            "stage": stage_name,
            "saved_at_utc": ts,
            "payload": payload,
        }

        checkpoint_path = os.path.join(session_dir, f"{stage_name}.json")
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        latest_path = os.path.join(session_dir, "latest.json")
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return checkpoint_path

    def list_sessions(self) -> List[str]:
        if not os.path.exists(self.checkpoints_dir):
            return []
        return sorted(
            [
                d for d in os.listdir(self.checkpoints_dir)
                if os.path.isdir(os.path.join(self.checkpoints_dir, d))
            ],
            reverse=True,
        )

    def list_session_checkpoints(self, session_id: str) -> List[str]:
        session_dir = os.path.join(self.checkpoints_dir, session_id)
        if not os.path.exists(session_dir):
            return []
        files = [
            f[:-5] for f in os.listdir(session_dir)
            if f.endswith(".json") and f != "latest.json"
        ]
        # Ordena según el orden oficial definido en settings.json si existe
        stage_order = self.settings.get("stages", [])
        order_map = {name: idx for idx, name in enumerate(stage_order)}
        return sorted(files, key=lambda s: order_map.get(s, 999))

    def load_checkpoint(self, session_id: str, stage_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        session_dir = os.path.join(self.checkpoints_dir, session_id)
        if not os.path.exists(session_dir):
            return None

        target_file = "latest.json" if stage_name is None else f"{stage_name}.json"
        path = os.path.join(session_dir, target_file)
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def append_history(self, session_id: str, event_type: str, details: Dict[str, Any]) -> str:
        history_file = os.path.join(self.history_dir, f"{session_id}_history.jsonl")
        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "event": event_type,
            "details": details,
        }
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return history_file