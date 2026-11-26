import random
from typing import Any, Dict, List


SYSTEM_PROMPT_EN = """
You are a Lead Procedural Terrain Architect for a multiplayer RPG featuring multiple playable races and skill-based combat.
Your job is to propose deterministic continent configuration options for Unity.

STRICT RULES:
1. NO LITERAL COPYING: Treat the user's reference strictly as creative/regional inspiration. Randomize seeds, exact coordinates, and regional proportions so the result is not a literal copy.
2. BARE CONTINENT ONLY: Output ONLY terrain parameters, noise layers, dimensions, and flat zones for future cities/towns. Do NOT place or include vegetation, trees, rocks, props, buildings, towns, or NPCs.
3. FIXED WORLD VIA SEED: Always assign an explicit integer seed so the generated map remains fixed and reproducible across sessions, servers, and clients.
4. OCEAN BOUNDARY / CONTINENT ISOLATION: Ensure the landmass is framed as a continent with water/ocean margins rather than a raw infinite box with abrupt edges.
5. FLAT ZONES FOR CITIES & TOWNS: Reserve flat zones with smooth blend margins and gentle slopes so racial cities and towns can be placed later without floating or sinking geometry.
6. SKILL-COMBAT READABILITY: Favor clear elevation transitions and avoid chaotic micro-spikes in main traversal areas so movement, line of sight, and AOE/skill mechanics work reliably.
"""


def generate_continent_options(
    reference_text: str,
    selected_skills: List[str],
    selected_mcp: List[str],
    base_seed: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Generates 3 distinct, randomized continent configuration options inspired by
    `reference_text` without copying it literally.
    """
    rng = random.Random(base_seed) if base_seed is not None else random.SystemRandom()

    def rand_seed() -> int:
        return rng.randint(100000, 9999999)

    combat_smooth = "skill_combat_readable_topography" in selected_skills
    max_ridge_weight = 0.25 if combat_smooth else 0.35

    opt_1 = {
        "option_id": "opt_1_central_plains_and_rim",
        "title": "Option 1: Broad Central Plains with Outer Mountain Rim",
        "summary": (
            f"Randomized continent inspired by '{reference_text}' with a wide central plain "
            f"for multi-race hubs and elevated outer ridges. Active skills: {selected_skills}. "
            f"Active MCP: {selected_mcp}."
        ),
        "parameters": {
            "world_seed": rand_seed(),
            "dimensions": {"width_meters": 8192, "length_meters": 8192, "max_height_meters": 700.0},
            "ocean_border_mask": {"enabled": True, "margin_meters": 650.0, "falloff": "smoothstep"},
            "noise_layers": [
                {
                    "layer_name": "Continental_Mass",
                    "noise_type": "Perlin",
                    "scale": 0.00065,
                    "octaves": 5,
                    "persistence": 0.5,
                    "lacunarity": 2.0,
                    "weight": 0.72,
                },
                {
                    "layer_name": "Outer_Ridges",
                    "noise_type": "RigidMultifractal",
                    "scale": 0.0032,
                    "octaves": 5,
                    "persistence": 0.45,
                    "lacunarity": 2.05,
                    "weight": max_ridge_weight,
                },
            ],
            "city_flat_zones": [
                {
                    "zone_id": "central_realm_hub",
                    "center_coordinates": {"x": rng.randint(3600, 4500), "z": rng.randint(3600, 4500)},
                    "radius_meters": 240.0,
                    "target_elevation_meters": 60.0,
                    "blend_margin_meters": 55.0,
                    "max_slope": 0.015,
                },
                {
                    "zone_id": "northern_highland_outpost",
                    "center_coordinates": {"x": rng.randint(2500, 5600), "z": rng.randint(5800, 6600)},
                    "radius_meters": 160.0,
                    "target_elevation_meters": 135.0,
                    "blend_margin_meters": 40.0,
                    "max_slope": 0.02,
                },
                {
                    "zone_id": "southern_coast_settlement",
                    "center_coordinates": {"x": rng.randint(2500, 5600), "z": rng.randint(1500, 2300)},
                    "radius_meters": 180.0,
                    "target_elevation_meters": 18.0,
                    "blend_margin_meters": 40.0,
                    "max_slope": 0.02,
                },
            ],
        },
    }

    opt_2 = {
        "option_id": "opt_2_split_basins_and_highlands",
        "title": "Option 2: Twin Basins Separated by a Central Highland Spine",
        "summary": (
            f"Randomized variation inspired by '{reference_text}' splitting two large basins "
            f"across a central spine with 4 flat city slots. Active skills: {selected_skills}. "
            f"Active MCP: {selected_mcp}."
        ),
        "parameters": {
            "world_seed": rand_seed(),
            "dimensions": {"width_meters": 8192, "length_meters": 8192, "max_height_meters": 800.0},
            "ocean_border_mask": {"enabled": True, "margin_meters": 700.0, "falloff": "smoothstep"},
            "noise_layers": [
                {
                    "layer_name": "Twin_Landmass_Base",
                    "noise_type": "Simplex",
                    "scale": 0.00075,
                    "octaves": 6,
                    "persistence": 0.52,
                    "lacunarity": 2.0,
                    "weight": 0.70,
                },
                {
                    "layer_name": "Spine_Elevations",
                    "noise_type": "RigidMultifractal",
                    "scale": 0.0038,
                    "octaves": 5,
                    "persistence": 0.46,
                    "lacunarity": 2.1,
                    "weight": max_ridge_weight,
                },
            ],
            "city_flat_zones": [
                {
                    "zone_id": "west_basin_city",
                    "center_coordinates": {"x": rng.randint(1800, 2800), "z": rng.randint(3200, 5000)},
                    "radius_meters": 210.0,
                    "target_elevation_meters": 45.0,
                    "blend_margin_meters": 45.0,
                    "max_slope": 0.02,
                },
                {
                    "zone_id": "east_basin_city",
                    "center_coordinates": {"x": rng.randint(5300, 6300), "z": rng.randint(3200, 5000)},
                    "radius_meters": 210.0,
                    "target_elevation_meters": 50.0,
                    "blend_margin_meters": 45.0,
                    "max_slope": 0.02,
                },
                {
                    "zone_id": "north_pass_town",
                    "center_coordinates": {"x": rng.randint(3500, 4600), "z": rng.randint(5800, 6500)},
                    "radius_meters": 150.0,
                    "target_elevation_meters": 120.0,
                    "blend_margin_meters": 35.0,
                    "max_slope": 0.02,
                },
                {
                    "zone_id": "south_bay_port",
                    "center_coordinates": {"x": rng.randint(3500, 4600), "z": rng.randint(1600, 2300)},
                    "radius_meters": 170.0,
                    "target_elevation_meters": 15.0,
                    "blend_margin_meters": 35.0,
                    "max_slope": 0.02,
                },
            ],
        },
    }

    opt_3 = {
        "option_id": "opt_3_wide_archipelago_core",
        "title": "Option 3: Compact Continent Core with Deep Bays & Terraced Flats",
        "summary": (
            f"Randomized interpretation inspired by '{reference_text}' with a compact continent core "
            f"and 3 flat slots for settlements. Active skills: {selected_skills}. "
            f"Active MCP: {selected_mcp}."
        ),
        "parameters": {
            "world_seed": rand_seed(),
            "dimensions": {"width_meters": 6144, "length_meters": 6144, "max_height_meters": 650.0},
            "ocean_border_mask": {"enabled": True, "margin_meters": 600.0, "falloff": "smoothstep"},
            "noise_layers": [
                {
                    "layer_name": "Core_Continent",
                    "noise_type": "Perlin",
                    "scale": 0.0009,
                    "octaves": 4,
                    "persistence": 0.48,
                    "lacunarity": 2.0,
                    "weight": 0.75,
                },
                {
                    "layer_name": "Terrace_Ridges",
                    "noise_type": "Simplex",
                    "scale": 0.0028,
                    "octaves": 5,
                    "persistence": 0.45,
                    "lacunarity": 2.0,
                    "weight": max_ridge_weight,
                },
            ],
            "city_flat_zones": [
                {
                    "zone_id": "heartland_capital",
                    "center_coordinates": {"x": rng.randint(2700, 3400), "z": rng.randint(2700, 3400)},
                    "radius_meters": 200.0,
                    "target_elevation_meters": 55.0,
                    "blend_margin_meters": 45.0,
                    "max_slope": 0.015,
                },
                {
                    "zone_id": "frontier_ridge_town",
                    "center_coordinates": {"x": rng.randint(1800, 4300), "z": rng.randint(4300, 4900)},
                    "radius_meters": 145.0,
                    "target_elevation_meters": 110.0,
                    "blend_margin_meters": 35.0,
                    "max_slope": 0.02,
                },
                {
                    "zone_id": "harbor_flat_slot",
                    "center_coordinates": {"x": rng.randint(1800, 4300), "z": rng.randint(1200, 1800)},
                    "radius_meters": 165.0,
                    "target_elevation_meters": 10.0,
                    "blend_margin_meters": 35.0,
                    "max_slope": 0.02,
                },
            ],
        },
    }

    return [opt_1, opt_2, opt_3]


def build_change_items(old_params: Dict[str, Any], new_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Breaks a proposed parameter set into individual change items so the user can
    select which specific changes to approve or reject.
    """
    items: List[Dict[str, Any]] = []
    keys = [
        "world_seed",
        "dimensions",
        "ocean_border_mask",
        "noise_layers",
        "city_flat_zones",
    ]
    for idx, key in enumerate(keys, start=1):
        before = old_params.get(key)
        after = new_params.get(key)
        if before != after:
            items.append(
                {
                    "index": idx,
                    "field": key,
                    "before": before,
                    "after": after,
                }
            )
    return items