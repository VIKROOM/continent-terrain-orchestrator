import json
import os
from typing import Any, Dict, List, Optional
from state_manager import StateManager
from recovery import RecoveryManager
from planner_and_selection import (
    SYSTEM_PROMPT_EN,
    generate_continent_options,
    build_change_items,
)


class TerrainOrchestrator:
    def __init__(self, base_dir: str = "."):
        self.sm = StateManager(base_dir=base_dir)
        self.recovery = RecoveryManager(self.sm)

    def stage_1_foundation_check(self, session_id: str) -> Dict[str, Any]:
        unity_root = self.sm.settings["unity_project_root"]
        target_file = self.sm.get_unity_target_config_path()
        unity_exists = os.path.isdir(unity_root)
        assets_exists = os.path.isdir(os.path.join(unity_root, "Assets"))

        if not unity_exists or not assets_exists:
            raise FileNotFoundError(
                f"Unity project foundation check failed. Verify 'unity_project_root' in config/settings.json: {unity_root}"
            )

        existing_config = {}
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                existing_config = json.load(f)

        state_payload = {
            "unity_project_root": unity_root,
            "target_file": target_file,
            "target_exists": os.path.exists(target_file),
            "existing_config": existing_config,
            "available_skills": self.sm.skills_catalog.get("skills", []),
            "available_mcp": self.sm.mcp_catalog.get("mcp_servers", []),
            "system_prompt_en": SYSTEM_PROMPT_EN.strip(),
        }
        self.sm.save_checkpoint(session_id, "foundation_check", state_payload)
        self.sm.append_history(session_id, "stage_completed", {"stage": "foundation_check"})
        return state_payload

    def stage_2_reference_and_options(
        self,
        session_id: str,
        foundation_state: Dict[str, Any],
        reference_text: str,
        selected_skills: List[str],
        selected_mcp: List[str],
        base_seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        options = generate_continent_options(
            reference_text=reference_text,
            selected_skills=selected_skills,
            selected_mcp=selected_mcp,
            base_seed=base_seed,
        )
        state_payload = {
            **foundation_state,
            "reference_text": reference_text,
            "selected_skills": selected_skills,
            "selected_mcp": selected_mcp,
            "options": options,
        }
        self.sm.save_checkpoint(session_id, "reference_and_options", state_payload)
        self.sm.append_history(
            session_id,
            "stage_completed",
            {
                "stage": "reference_and_options",
                "selected_skills": selected_skills,
                "selected_mcp": selected_mcp,
                "options_count": len(options),
            },
        )
        return state_payload

    def stage_3_selection_gate(
        self,
        session_id: str,
        options_state: Dict[str, Any],
        chosen_option_index: int,
    ) -> Dict[str, Any]:
        options = options_state["options"]
        if chosen_option_index < 0 or chosen_option_index >= len(options):
            raise ValueError("Invalid option index selected.")

        chosen_option = options[chosen_option_index]
        old_params = options_state.get("existing_config", {}).get("parameters", {})
        new_params = chosen_option["parameters"]
        change_items = build_change_items(old_params=old_params, new_params=new_params)

        state_payload = {
            **options_state,
            "chosen_option": chosen_option,
            "change_items": change_items,
        }
        self.sm.save_checkpoint(session_id, "selection_gate", state_payload)
        self.sm.append_history(
            session_id,
            "stage_completed",
            {
                "stage": "selection_gate",
                "chosen_option_id": chosen_option["option_id"],
                "pending_changes": [c["field"] for c in change_items],
            },
        )
        return state_payload

    def stage_4_diff_and_approval(
        self,
        session_id: str,
        selection_state: Dict[str, Any],
        approved_indices: List[int],
    ) -> Dict[str, Any]:
        change_items = selection_state["change_items"]
        existing_config = selection_state.get("existing_config", {})
        merged_params = dict(existing_config.get("parameters", {}))

        approved_fields = []
        rejected_fields = []

        for item in change_items:
            if item["index"] in approved_indices:
                merged_params[item["field"]] = item["after"]
                approved_fields.append(item["field"])
            else:
                rejected_fields.append(item["field"])

        final_document = {
            "target_file_path": self.sm.settings["target_terrain_config_relpath"],
            "change_summary": selection_state["chosen_option"]["summary"],
            "active_skills": selection_state["selected_skills"],
            "active_mcp": selection_state["selected_mcp"],
            "approved_changes": approved_fields,
            "rejected_changes": rejected_fields,
            "parameters": merged_params,
        }

        state_payload = {
            **selection_state,
            "approved_indices": approved_indices,
            "approved_fields": approved_fields,
            "rejected_fields": rejected_fields,
            "final_document": final_document,
        }
        self.sm.save_checkpoint(session_id, "diff_and_approval", state_payload)
        self.sm.append_history(
            session_id,
            "changes_reviewed",
            {
                "approved_fields": approved_fields,
                "rejected_fields": rejected_fields,
            },
        )
        return state_payload

    def stage_5_apply_changes(
        self,
        session_id: str,
        approval_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        approved_fields = approval_state.get("approved_fields", [])
        target_file = approval_state["target_file"]

        if not approved_fields:
            state_payload = {
                **approval_state,
                "written_to_disk": False,
                "message": "No changes approved. Unity files left untouched.",
            }
            self.sm.save_checkpoint(session_id, "apply_changes", state_payload)
            return state_payload

        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(approval_state["final_document"], f, indent=2, ensure_ascii=False)

        state_payload = {
            **approval_state,
            "written_to_disk": True,
            "message": f"Updated {target_file} with approved fields: {approved_fields}",
        }
        self.sm.save_checkpoint(session_id, "apply_changes", state_payload)
        self.sm.append_history(
            session_id,
            "file_written",
            {
                "target_file": target_file,
                "approved_fields": approved_fields,
            },
        )
        return state_payload

    def stage_6_unity_handoff(
        self,
        session_id: str,
        apply_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        handoff_instructions = {
            "unity_target_json": apply_state["target_file"],
            "written_to_disk": apply_state.get("written_to_disk", False),
            "next_step_in_unity": (
                "Run the Unity Terrain Bake script to read continent_master.json, "
                "generate the fixed-seed Perlin/FBM heightmap with flat city zones, "
                "and save the static TerrainData asset (no vegetation/rocks/buildings)."
            ),
        }
        state_payload = {
            **apply_state,
            "handoff": handoff_instructions,
        }
        self.sm.save_checkpoint(session_id, "unity_handoff", state_payload)
        self.sm.append_history(session_id, "stage_completed", {"stage": "unity_handoff"})
        return state_payload