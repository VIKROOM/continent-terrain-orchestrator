from typing import Any, Dict, Optional
from state_manager import StateManager


class RecoveryManager:
    def __init__(self, state_manager: StateManager):
        self.sm = state_manager

    def can_recover(self) -> bool:
        return bool(self.sm.settings.get("recovery", {}).get("allow_rollback_to_checkpoint", True))

    def recover_session(
        self,
        session_id: str,
        target_stage: Optional[str] = None,
        reason: str = "manual_recovery",
    ) -> Optional[Dict[str, Any]]:
        if not self.can_recover():
            raise RuntimeError("Rollback / recovery is disabled in config/settings.json")

        checkpoint = self.sm.load_checkpoint(session_id=session_id, stage_name=target_stage)
        if not checkpoint:
            return None

        self.sm.append_history(
            session_id=session_id,
            event_type="recovery_loaded",
            details={
                "recovered_from_stage": checkpoint.get("stage"),
                "requested_stage": target_stage or "latest",
                "reason": reason,
            },
        )
        return checkpoint