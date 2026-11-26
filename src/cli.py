import json
from i18n import get_text
from orchestrator import TerrainOrchestrator


def choose_language(default_lang: str = "es") -> str:
    raw = input(get_text(default_lang, "lang_prompt")).strip().lower()
    if raw in ("2", "en", "english", "ingles", "inglés"):
        return "en"
    if raw in ("1", "es", "spanish", "espanol", "español"):
        return "es"
    return default_lang


def prompt_multi_select(lang: str, title: str, items: list, default_ids: list) -> list:
    print(f"\n--- {title} ---")
    if not items:
        print(get_text(lang, "no_items"))
        return []

    default_label = "default" if lang == "en" else "por defecto"
    opt_label = "optional" if lang == "en" else "opcional"

    for idx, item in enumerate(items, start=1):
        mark = default_label if item["id"] in default_ids else opt_label
        print(f"  [{idx}] {item['id']} ({mark}) - {item['description']}")

    raw = input(get_text(lang, "multi_prompt")).strip().lower()
    if raw == "none":
        return []
    if raw == "all":
        return [item["id"] for item in items]
    if not raw:
        return list(default_ids)

    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            i = int(part) - 1
            if 0 <= i < len(items):
                item_id = items[i]["id"]
                if item_id not in selected:
                    selected.append(item_id)
            else:
                print(get_text(lang, "warn_range", part=part))
        else:
            print(get_text(lang, "warn_invalid", part=part))
    return selected


def prompt_index(lang: str, prompt_text: str, max_len: int, default_idx: int = 0) -> int:
    if max_len <= 0:
        return 0
    raw = input(prompt_text).strip()
    if not raw:
        return default_idx
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < max_len:
            return idx
    print(get_text(lang, "warn_select", raw=raw, default=default_idx + 1))
    return default_idx


def run_from_stage(orch: TerrainOrchestrator, lang: str, session_id: str, start_stage: str, state: dict):
    stages = orch.sm.settings["stages"]
    start_idx = stages.index(start_stage) if start_stage in stages else 0

    if start_idx <= 0:
        print(get_text(lang, "s1_title"))
        state = orch.stage_1_foundation_check(session_id)
        print(get_text(lang, "s1_target", target_file=state["target_file"]))

    if start_idx <= 1:
        print(get_text(lang, "s2_title"))
        ref = input(get_text(lang, "ref_prompt")).strip()
        if not ref:
            ref = get_text(lang, "default_ref")

        selected_skills = prompt_multi_select(
            lang,
            get_text(lang, "select_skills"),
            state["available_skills"],
            orch.sm.settings.get("default_enabled_skills", []),
        )
        selected_mcp = prompt_multi_select(
            lang,
            get_text(lang, "select_mcp"),
            state["available_mcp"],
            orch.sm.settings.get("default_enabled_mcp", []),
        )

        state = orch.stage_2_reference_and_options(
            session_id=session_id,
            foundation_state=state,
            reference_text=ref,
            selected_skills=selected_skills,
            selected_mcp=selected_mcp,
        )

    if start_idx <= 2:
        print(get_text(lang, "s3_title"))
        options = state["options"]
        for idx, opt in enumerate(options, start=1):
            print(f"\n  ({idx}) {opt['title']}")
            print(
                get_text(
                    lang,
                    "opt_meta",
                    seed=opt["parameters"]["world_seed"],
                    slots=len(opt["parameters"]["city_flat_zones"]),
                )
            )
            print(f"      {opt['summary']}")

        chosen_idx = prompt_index(
            lang,
            get_text(lang, "choose_opt", count=len(options)),
            len(options),
            default_idx=0,
        )
        state = orch.stage_3_selection_gate(session_id, state, chosen_idx)

    if start_idx <= 3:
        print(get_text(lang, "s4_title"))
        print(get_text(lang, "target_modify", target_file=state["target_file"]))
        change_items = state["change_items"]

        if not change_items:
            print(get_text(lang, "no_diffs"))
            approved_indices = []
        else:
            for item in change_items:
                print(get_text(lang, "change_item", index=item["index"], field=item["field"]))
                print(get_text(lang, "before", val=json.dumps(item["before"])))
                print(get_text(lang, "after", val=json.dumps(item["after"])))

            sel = input(get_text(lang, "approve_prompt")).strip().lower()
            valid_indices = {c["index"] for c in change_items}
            if sel == "all":
                approved_indices = [c["index"] for c in change_items]
            elif sel == "none" or not sel:
                approved_indices = []
            else:
                approved_indices = []
                for x in sel.split(","):
                    token = x.strip()
                    if token.isdigit() and int(token) in valid_indices:
                        approved_indices.append(int(token))
                    elif token:
                        print(get_text(lang, "warn_change", token=token))

        state = orch.stage_4_diff_and_approval(session_id, state, approved_indices)

    if start_idx <= 4:
        print(get_text(lang, "s5_title"))
        state = orch.stage_5_apply_changes(session_id, state)
        print(get_text(lang, "s5_result", msg=state["message"]))

    if start_idx <= 5:
        print(get_text(lang, "s6_title"))
        state = orch.stage_6_unity_handoff(session_id, state)
        print(get_text(lang, "s6_done", session_id=session_id))


def main():
    orch = TerrainOrchestrator(".")
    default_lang = orch.sm.settings.get("default_language", "es")
    lang = choose_language(default_lang)

    print(get_text(lang, "banner"))
    mode = input(get_text(lang, "mode_prompt")).strip()

    if mode == "2":
        sessions = orch.sm.list_sessions()
        if not sessions:
            print(get_text(lang, "no_sessions"))
            session_id = orch.sm.new_session_id()
            run_from_stage(orch, lang, session_id, "foundation_check", {})
            return

        print(get_text(lang, "avail_sessions"))
        for idx, s in enumerate(sessions, start=1):
            print(f"  [{idx}] {s}")
        s_idx = prompt_index(lang, get_text(lang, "select_session", default=1), len(sessions), default_idx=0)
        session_id = sessions[s_idx]

        checkpoints = orch.sm.list_session_checkpoints(session_id)
        print(get_text(lang, "saved_cps", session_id=session_id, checkpoints=checkpoints))
        cp_stage = input(get_text(lang, "cp_prompt")).strip() or None

        recovered = orch.recovery.recover_session(session_id, target_stage=cp_stage, reason="cli_recovery")
        if not recovered:
            print(get_text(lang, "cp_not_found"))
            return

        stages = orch.sm.settings["stages"]
        rec_stage = recovered["stage"]
        next_idx = min(stages.index(rec_stage) + 1, len(stages) - 1)
        next_stage = stages[next_idx]
        print(get_text(lang, "recovered_msg", rec_stage=rec_stage, next_stage=next_stage))
        run_from_stage(orch, lang, session_id, next_stage, recovered["payload"])
    else:
        session_id = orch.sm.new_session_id()
        print(get_text(lang, "new_session", session_id=session_id))
        run_from_stage(orch, lang, session_id, "foundation_check", {})


if __name__ == "__main__":
    main()