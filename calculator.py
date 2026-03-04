from __future__ import annotations
from typing import Any, Dict, List, Mapping
from models import siege, DragonInfo, TroopType, attackBattleStats, defenseBattleStats
from data import load_troopBaseData, load_dragonBaseData, load_damageModifiers, load_maxedStats, load_siegestats, load_sophealth
from helpers import *
import math
from models import _to_float


_TROOPTYPE_TO_JSON = {
    TroopType.INFANTRY: "Infantry",
    TroopType.RANGED: "Ranged",
    TroopType.CAVALRY: "Cavalry",
}

_TROOPTYPE_TO_TROOPKEY_PREFIX = {
    TroopType.INFANTRY: "Infantry",
    TroopType.RANGED: "Ranged",
    TroopType.CAVALRY: "Cavalry",
}


def _normalize_troop_type(tt: Any) -> TroopType:
    """Accept TroopType or strings like 'inf', 'rng', 'cav'."""
    if isinstance(tt, TroopType):
        return tt
    if isinstance(tt, str):
        return TroopType(tt.lower().strip())
    raise TypeError(f"troop_type must be TroopType or str, got {type(tt)}")

def calc_wall_damage(
    siege_input,  # models.siege instance
    sop_stars: Any,
    siege_by_tier: Mapping[int, Any],   # from load_siegestats()
    sop_by_star: Mapping[Any, Any],     # from load_sophealth()
) -> dict:


    tier = siege_input.tier
    march_size = siege_input.msize
    wdb_pp = siege_input.wdb  # percent points (20 => +20%)

    # ---- lookups ----
    if tier not in siege_by_tier:
        raise KeyError(f"Unknown siege tier: {tier}. Available: {sorted(siege_by_tier.keys())}")

    tier_row = siege_by_tier[tier]
    base_damage = float(tier_row.damage)  # StatObject => "Damage" -> damage

    # normalize stars key to match dict keys (they came from JSON as numbers)
    stars_key = _to_float(sop_stars, default=None)
    if stars_key is None:
        raise ValueError(f"Invalid sop_stars: {sop_stars}")

    sop_row = sop_by_star.get(stars_key)
    if sop_row is None:
        # sometimes dict keys could be int if JSON had "5" and python parsed as int
        if float(stars_key).is_integer():
            sop_row = sop_by_star.get(int(stars_key))

    if sop_row is None:
        raise KeyError(f"Unknown SoP stars: {sop_stars}. Available: {sorted(sop_by_star.keys())}")

    sop_health = float(sop_row.wall)  # StatObject => "Wall" -> wall
    if sop_health <= 0:
        raise ValueError(f"SoP wall health must be > 0. Got: {sop_health}")

    # ---- calculation ----
    raw_damage = march_size * base_damage * (1.0 + (wdb_pp / 100.0))
    percent_damage = raw_damage / sop_health

    remaining_wall = max(0.0, sop_health - raw_damage)
    hits_to_break = math.inf if raw_damage <= 0 else math.ceil(sop_health / raw_damage)

    return {
        "inputs": {
            "tier": tier,
            "march_size": march_size,
            "wdb_percent_points": wdb_pp,
            "sop_stars": stars_key,
        },
        "lookups": {
            "base_damage": base_damage,
            "sop_health": sop_health,
        },
        "results": {
            "raw_damage": raw_damage,
            "percent_damage": percent_damage,          # fraction (0.10 = 10%)
            "percent_damage_pct": percent_damage * 100.0,
            "remaining_wall": remaining_wall,
            "hits_to_break": hits_to_break,
        },
    }


def compute_battle_like_sheet(
    attackers: List[attackBattleStats],
    defenders: List[defenseBattleStats],
    *,
    scenario: str,
) -> Dict:
    """
    Works like your Google Sheet.

    Inputs:
      attackers: list of attacker marches (usually 1 per type in full rally)
      defenders: list of defender marches (usually 1 per type in full rein)

    Scenario behavior:
      - fullrally_vs_fullrein: uses attackers list and defenders list as provided
      - solo_vs_fullrein: expects attackers has exactly 1 march; defenders can be 1..N
      - fullrally_vs_solorein: attackers can be 1..N; defenders should have exactly 1 march

    Returns:
      - per-attacker "Att vs X" values
      - per-defender "Total Health" and "Total Def vs X" values
      - killed_matrix[att_type][def_type]
      - totals killed per defender type (your bottom totals)
      - total killed overall
    """
    scenario = str(scenario).lower().strip()
    allowed = {"fullrally_vs_fullrein", "solo_vs_fullrein", "fullrally_vs_solorein"}
    if scenario not in allowed:
        raise ValueError(f"scenario must be one of: {', '.join(sorted(allowed))}")

    if not attackers or not defenders:
        raise ValueError("attackers and defenders must be non-empty lists")

    if scenario == "solo_vs_fullrein" and len(attackers) != 1:
        raise ValueError("solo_vs_fullrein expects exactly 1 attacker march in attackers list")
    if scenario == "fullrally_vs_solorein" and len(defenders) != 1:
        raise ValueError("fullrally_vs_solorein expects exactly 1 defender march in defenders list")

    troops = load_troopBaseData()
    mods = load_damageModifiers()
    if not troops:
        raise RuntimeError("TroopBaseStats.json did not load (empty dict).")
    if not mods:
        raise RuntimeError("DamageModifiers.json did not load (empty dict).")

    def troop_key(tt: TroopType, tier: int) -> str:
        return f"{_TROOPTYPE_TO_TROOPKEY_PREFIX[tt]}_{tier}"

    def dmg_mod(tier: int, src_tt: TroopType, tgt_tt: TroopType) -> float:
        tier_key = f"T{tier}"
        src_json = _TROOPTYPE_TO_JSON[src_tt]
        tgt_json = _TROOPTYPE_TO_JSON[tgt_tt]
        return float(mods[tier_key][src_json][tgt_json])

    def atk_vs(att: attackBattleStats, tgt_tt: TroopType) -> float:
        # percent points -> fraction
        if tgt_tt == TroopType.INFANTRY:
            return att.attvsinf / 100.0
        if tgt_tt == TroopType.RANGED:
            return att.attvsrng / 100.0
        return att.attvscav / 100.0

    def def_vs(defn: defenseBattleStats, tgt_tt: TroopType) -> float:
        # percent points -> fraction
        if tgt_tt == TroopType.INFANTRY:
            return defn.defvsinf / 100.0
        if tgt_tt == TroopType.RANGED:
            return defn.defvsrng / 100.0
        return defn.defvscav / 100.0

    # --- build sheet-like per-march derived values ---
    attacker_rows = []
    for a in attackers:
        ttA = a.TroopType
        tierA = int(a.TroopTier)
        if tierA <= 0:
            raise ValueError("attacker TroopTier must be > 0")
        keyA = troop_key(ttA, tierA)
        if keyA not in troops:
            raise KeyError(f"Missing attacker troop '{keyA}' in TroopBaseStats.json")

        tA = troops[keyA]
        base_atk = float(getattr(tA, "attack"))
        rngA = int(getattr(tA, "range"))

        atk_mul = 1.0 + (a.baseAttackBuff / 100.0) + (a.marcherAttackBuff / 100.0)

        # Sheet columns: Att vs Inf/Cav/Ranged (these are "totalattack_vst" before mods)
        att_vs_inf = base_atk * atk_mul * (1.0 + atk_vs(a, TroopType.INFANTRY))
        att_vs_cav = base_atk * atk_mul * (1.0 + atk_vs(a, TroopType.CAVALRY))
        att_vs_rng = base_atk * atk_mul * (1.0 + atk_vs(a, TroopType.RANGED))

        attacker_rows.append({
            "type": ttA,
            "type_json": _TROOPTYPE_TO_JSON[ttA],
            "tier": tierA,
            "msize": int(a.msizeAtt),
            "base_atk": base_atk,
            "range": rngA,
            "att_vs": {
                "Infantry": att_vs_inf,
                "Cavalry": att_vs_cav,
                "Ranged": att_vs_rng,
            }
        })

    defender_rows = []
    for d in defenders:
        ttD = d.TroopType
        tierD = int(d.TroopTier)
        if tierD <= 0:
            raise ValueError("defender TroopTier must be > 0")
        keyD = troop_key(ttD, tierD)
        if keyD not in troops:
            raise KeyError(f"Missing defender troop '{keyD}' in TroopBaseStats.json")

        tD = troops[keyD]
        base_def = float(getattr(tD, "defense"))
        base_hp = float(getattr(tD, "health"))
        rngD = int(getattr(tD, "range"))

        # Sheet: Total Health is a multiplicative boost on HP
        hp_mul = 1.0 + (d.baseHealthBuff / 100.0) + (d.healthatsopBuff / 100.0) + (d.defenderhealthbuff / 100.0)
        total_hp = base_hp * hp_mul

        # Sheet: Defense boosts multiplier (no marcher here per your defender definition)
        def_mul = 1.0 + (d.baseDefenseBuff / 100.0) + (d.defenseatsopBuff / 100.0) + (d.defenderdefensebuff / 100.0)

        # Sheet columns: "Total Def vs X" = total_hp * (base_def * def_mul * (1+defvsX))
        totaldef_vs_inf = total_hp * (base_def * def_mul * (1.0 + def_vs(d, TroopType.INFANTRY)))
        totaldef_vs_cav = total_hp * (base_def * def_mul * (1.0 + def_vs(d, TroopType.CAVALRY)))
        totaldef_vs_rng = total_hp * (base_def * def_mul * (1.0 + def_vs(d, TroopType.RANGED)))

        defender_rows.append({
            "type": ttD,
            "type_json": _TROOPTYPE_TO_JSON[ttD],
            "tier": tierD,
            "msize": int(d.msizeDef),
            "base_def": base_def,
            "range": rngD,
            "total_hp": total_hp,
            "totaldef_vs": {
                "Infantry": totaldef_vs_inf,
                "Cavalry": totaldef_vs_cav,
                "Ranged": totaldef_vs_rng,
            }
        })

    # --- battle matrix like your sheet ---
    killed_matrix = {
        "Infantry": {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
        "Cavalry":  {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
        "Ranged":   {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
    }
    killed_by_def_type = {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0}
    killed_by_att_type = {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0}

    for A in attacker_rows:
        att_tt = A["type"]
        att_name = A["type_json"]

        for D in defender_rows:
            def_tt = D["type"]
            def_name = D["type_json"]

            # attacker selects correct "Att vs <defender type>"
            atk_val = A["att_vs"][def_name]  # sheet "Att vs X"

            # defender selects correct "Total Def vs <attacker type>"
            def_val = D["totaldef_vs"][att_name]  # sheet "Total Def vs X"

            # modifiers
            dmgA = dmg_mod(A["tier"], att_tt, def_tt)
            dmgD = dmg_mod(D["tier"], def_tt, att_tt)

            tmodA = tiermodifier(A["tier"], D["tier"])
            tmodD = tiermodifier(D["tier"], A["tier"])

            rmod = rangemodifier(A["range"], D["range"])

            # EXACT sheet-like kill formula
            num = (A["msize"] ** 2) * atk_val * dmgA * tmodA * rmod
            den = (D["msize"]) * def_val * tmodD * dmgD

            if den <= 0:
                continue

            killed = 4.0 * (num / den)

            killed_matrix[att_name][def_name] += killed
            killed_by_def_type[def_name] += killed
            killed_by_att_type[att_name] += killed

    total_killed = sum(killed_by_def_type.values())

    # Present like your sheet: integers for killed
    return {
        "scenario": scenario,

        "attackers": [
            {
                "TroopType": r["type_json"],
                "Tier": r["tier"],
                "MarchSize": r["msize"],
                "Att_vs_Inf": r["att_vs"]["Infantry"],
                "Att_vs_Cav": r["att_vs"]["Cavalry"],
                "Att_vs_Ranged": r["att_vs"]["Ranged"],
            }
            for r in attacker_rows
        ],
        "defenders": [
            {
                "TroopType": r["type_json"],
                "Tier": r["tier"],
                "MarchSize": r["msize"],
                "TotalHealth": r["total_hp"],
                "TotalDef_vs_Inf": r["totaldef_vs"]["Infantry"],
                "TotalDef_vs_Cav": r["totaldef_vs"]["Cavalry"],
                "TotalDef_vs_Ranged": r["totaldef_vs"]["Ranged"],
            }
            for r in defender_rows
        ],

        "killed_matrix": {a: {d: int(v) for d, v in row.items()} for a, row in killed_matrix.items()},
        "killed_by_defender_type": {k: int(v) for k, v in killed_by_def_type.items()},
        "killed_by_attacker_type": {k: int(v) for k, v in killed_by_att_type.items()},
        "killed_total": int(total_killed),
    }


def statsCalculator(atkbuff, marcheratkbuff, atkvscav, atkvsinf, atkvsrng, defbuff, healthbuff, defatsopbuff, healthatsopbuff, defvscav, defvsinf, defvsrng, defenderdefensebuff, defenderhealthbuff):
    totalatkvscav = ((1 + atkbuff/100 + marcheratkbuff/100) * (1 + atkvscav/100)) - 1
    totalatkvsinf = ((1 + atkbuff/100 + marcheratkbuff/100) * (1 + atkvsinf/100)) - 1
    totalatkvsrng = ((1 + atkbuff/100 + marcheratkbuff/100) * (1 + atkvsrng/100)) - 1

    totalhealth = (1 + healthbuff/100 + defenderhealthbuff/100 + healthatsopbuff/100) - 1
    totaldefvscav = ((1 + defbuff/100 + defenderdefensebuff/100 + defatsopbuff/100) * (1 + defvscav/100)) - 1
    totaldefvsinf = ((1 + defbuff/100 + defenderdefensebuff/100 + defatsopbuff/100) * (1 + defvsinf/100)) - 1
    totaldefvsrng = ((1 + defbuff/100 + defenderdefensebuff/100 + defatsopbuff/100) * (1 + defvsrng/100)) - 1

    r = lambda x: round(x, 2)

    return {
        "Total Attack vs Cavalry": r(totalatkvscav),
        "Total Attack vs Infantry": r(totalatkvsinf),
        "Total Attack vs Ranged": r(totalatkvsrng),
        "Total Health": r(totalhealth),
        "Total Defense vs Cavalry": r(totaldefvscav),
        "Total Defense vs Infantry": r(totaldefvsinf),
        "Total Defense vs Ranged": r(totaldefvsrng),
    }

def statsComparator(troop_type_json: str, attacker: dict, defender: dict) -> dict:
    """
    One player: attacker preset + defender preset, compared to MaxedStats.

    troop_type_json: "Infantry" | "Ranged" | "Cavalry"

    attacker dict expected keys (percent points):
      baseatkbuff, marcheratkbuff, atkvscav, atkvsinf, atkvsrng

    defender dict expected keys (percent points):
      basedefbuff, basehealthbuff, defatsopbuff, healthatsopbuff,
      defvscav, defvsinf, defvsrng, defdefensebuff, defhealthbuff

    Missing keys default to 0.0.
    """

    def g(d: dict, key: str) -> float:
        return float(d.get(key, 0.0))

    def pctdiff(x: float, ref: float) -> str:
        if ref == 0:
            return "0.00%"
        return f"{((x - ref) / ref) * 100:.2f}%"

    # ---- Load maxed ----
    maxed_all = load_maxedStats()
    if not maxed_all:
        raise RuntimeError("MaxedStats.json did not load (empty dict).")
    if troop_type_json not in maxed_all:
        raise KeyError(f"MaxedStats missing troop type '{troop_type_json}'.")

    maxed_entry = maxed_all[troop_type_json]
    max_atk = getattr(maxed_entry, "attack", None)
    max_def = getattr(maxed_entry, "defense", None)

    if not isinstance(max_atk, dict) or not isinstance(max_def, dict):
        raise TypeError("MaxedStats structure unexpected: expected Attack/Defense dict blocks.")

    # ---- Player attacker totals (defender-only fields = 0) ----
    attacker_totals = statsCalculator(
        g(attacker, "baseatkbuff"),
        g(attacker, "marcheratkbuff"),
        g(attacker, "atkvscav"),
        g(attacker, "atkvsinf"),
        g(attacker, "atkvsrng"),
        0.0,   # defbuff
        0.0,   # healthbuff
        0.0,   # defatsopbuff
        0.0,   # healthatsopbuff
        0.0,   # defvscav
        0.0,   # defvsinf
        0.0,   # defvsrng
        0.0,   # defenderdefensebuff
        0.0,   # defenderhealthbuff
    )

    # ---- Player defender totals (attacker-only fields = 0) ----
    defender_totals = statsCalculator(
        0.0,   # atkbuff
        0.0,   # marcheratkbuff
        0.0,   # atkvscav
        0.0,   # atkvsinf
        0.0,   # atkvsrng
        g(defender, "basedefbuff"),
        g(defender, "basehealthbuff"),
        g(defender, "defatsopbuff"),
        g(defender, "healthatsopbuff"),
        g(defender, "defvscav"),
        g(defender, "defvsinf"),
        g(defender, "defvsrng"),
        g(defender, "defdefensebuff"),
        g(defender, "defhealthbuff"),
    )

    # ---- Maxed attacker totals (defender-only fields = 0) ----
    maxed_attacker_totals = statsCalculator(
        float(max_atk.get("Attack", 0.0)),
        float(max_atk.get("MarcherAttack", 0.0)),
        float(max_atk.get("vsCav", 0.0)),
        float(max_atk.get("vsInf", 0.0)),
        float(max_atk.get("vsRanged", 0.0)),
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    )

    # ---- Maxed defender totals (attacker-only fields = 0) ----
    maxed_defender_totals = statsCalculator(
        0.0, 0.0, 0.0, 0.0, 0.0,
        float(max_def.get("Defense", 0.0)),
        float(max_def.get("Health", 0.0)),
        float(max_def.get("DefenseAtSop", 0.0)),
        float(max_def.get("HealthAtSop", 0.0)),
        float(max_def.get("vsCav", 0.0)),
        float(max_def.get("vsInf", 0.0)),
        float(max_def.get("vsRanged", 0.0)),
        float(max_def.get("DefenderDefense", 0.0)),
        float(max_def.get("DefenderHealth", 0.0)),
    )

    # ---- Compare only the relevant metrics for each preset ----
    # Attacker preset compares attack totals only
    attacker_keys = [
        "Total Attack vs Cavalry",
        "Total Attack vs Infantry",
        "Total Attack vs Ranged",
    ]

    # Defender preset compares health + defense totals
    defender_keys = [
        "Total Health",
        "Total Defense vs Cavalry",
        "Total Defense vs Infantry",
        "Total Defense vs Ranged",
    ]

    attacker_comp = {}
    for k in attacker_keys:
        attacker_comp[k] = {
            "player": attacker_totals[k],
            "maxed": maxed_attacker_totals[k],
            "diff_pct": pctdiff(float(attacker_totals[k]), float(maxed_attacker_totals[k])),
        }

    defender_comp = {}
    for k in defender_keys:
        defender_comp[k] = {
            "player": defender_totals[k],
            "maxed": maxed_defender_totals[k],
            "diff_pct": pctdiff(float(defender_totals[k]), float(maxed_defender_totals[k])),
        }

    return {
        "troop_type": troop_type_json,

        "attacker_true_power": attacker_totals,
        "defender_true_power": defender_totals,

        "maxed_attacker_true_power": maxed_attacker_totals,
        "maxed_defender_true_power": maxed_defender_totals,

        "comparison": {
            "attacker_vs_maxed": attacker_comp,
            "defender_vs_maxed": defender_comp,
        },
    }


def dvdcalc_duel(attacker: DragonInfo, defender: DragonInfo):
    """
    Dragon duel calculation: attacker -> defender

    Rules:
    - Buffs are percentage points (e.g., 1500 = 1500%)
    - regenrate is flat
    - Healing cost is based on the DEFENDER (the one taking damage)
    - Output is presentation-ready:
        * raw damage: integer part
        * percent damage: 'X.XX%'
        * gold values: integer part
    """

    dragons = load_dragonBaseData()

    if attacker.level not in dragons:
        raise KeyError(f"Attacker dragon level {attacker.level} not found.")
    if defender.level not in dragons:
        raise KeyError(f"Defender dragon level {defender.level} not found.")

    A = dragons[attacker.level]
    B = dragons[defender.level]

    # Apply buffs (percentage points → multipliers)
    A_atk_total = A.base_dvd_attack * (1.0 + attacker.atkbuff / 100.0)
    B_def_total = B.base_dvd_defense * (1.0 + defender.defbuff / 100.0)
    B_hp_total  = B.base_health      * (1.0 + defender.healthbuff / 100.0)

    # Core damage math (A -> B)
    raw_dmg = A_atk_total / B_def_total
    percent_dmg = raw_dmg / B_hp_total

    # Healing economics (defender side)
    heal_mult = B.healing_multiplier
    heal_exp  = B.healing_exponent

    if defender.regenrate <= 0:
        raise ValueError("defender.regenrate must be > 0")

    total_gold_full = heal_mult * (B_hp_total / defender.regenrate) ** heal_exp

    # === PRESENTATION NORMALIZATION ===
    return {
        "raw_damage": int(raw_dmg),                          # truncate
        "percent_damage": f"{percent_dmg * 100:.2f}%",      # formatted %
        "total_gold": int(total_gold_full),                  # truncate
    }