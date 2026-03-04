# combat_test_fullrally_vs_solorein.py
from __future__ import annotations

from calculator import compute_battle_like_sheet
from models import TroopType, attackBattleStats, defenseBattleStats


maxed = {
    "Infantry": {
        "Attack":  {"Attack": 1390.35, "MarcherAttack": 6873.38, "vsCav": 1610.51, "vsInf": 1097.48, "vsRanged": 346.15},
        "Defense": {"Defense": 1018.42, "Health": 365.07, "DefenseAtSop": 2600.58, "HealthAtSop": 2108.68, "DefenderDefense": 86.00, "DefenderHealth": 96.41, "vsCav": 917.99, "vsInf": 589.85, "vsRanged": 608.53},
    },
    "Ranged": {
        "Attack":  {"Attack": 1308.81, "MarcherAttack": 7415.18, "vsCav": 436.92, "vsInf": 1717.59, "vsRanged": 1483.16},
        "Defense": {"Defense": 1225.62, "Health": 438.98, "DefenseAtSop": 2720.27, "HealthAtSop": 2302.55, "DefenderDefense": 86.00, "DefenderHealth": 87.23, "vsCav": 838.02, "vsInf": 989.71, "vsRanged": 477.20},
    },
    "Cavalry": {
        "Attack":  {"Attack": 1317.48, "MarcherAttack": 7271.58, "vsCav": 1620.69, "vsInf": 471.49, "vsRanged": 1642.80},
        "Defense": {"Defense": 1197.68, "Health": 337.45, "DefenseAtSop": 2439.88, "HealthAtSop": 2842.28, "DefenderDefense": 86.00, "DefenderHealth": 45.00, "vsCav": 415.46, "vsInf": 1189.33, "vsRanged": 917.15},
    },
}

TT_MAP = {
    "Infantry": TroopType.INFANTRY,
    "Ranged": TroopType.RANGED,
    "Cavalry": TroopType.CAVALRY,
}


def make_att(tt_name: str, tier: int, msize: int) -> attackBattleStats:
    a = maxed[tt_name]["Attack"]
    return attackBattleStats(
        TroopType=TT_MAP[tt_name],
        TroopTier=tier,
        msizeAtt=msize,
        baseAttackBuff=a["Attack"],
        marcherAttackBuff=a["MarcherAttack"],
        attvscav=a["vsCav"],
        attvsinf=a["vsInf"],
        attvsrng=a["vsRanged"],
    )


def make_def(tt_name: str, tier: int, msize: int) -> defenseBattleStats:
    d = maxed[tt_name]["Defense"]
    return defenseBattleStats(
        TroopType=TT_MAP[tt_name],
        TroopTier=tier,
        msizeDef=msize,
        baseDefenseBuff=d["Defense"],
        baseHealthBuff=d["Health"],
        defenseatsopBuff=d["DefenseAtSop"],
        healthatsopBuff=d["HealthAtSop"],
        defenderdefensebuff=d["DefenderDefense"],
        defenderhealthbuff=d["DefenderHealth"],
        defvscav=d["vsCav"],
        defvsinf=d["vsInf"],
        defvsrng=d["vsRanged"],
    )


def pretty_print(title: str, res: dict):
    print(f"\n=== {title} ===")
    print("Killed by defender type:", res["killed_by_defender_type"])
    print("Killed matrix:", res["killed_matrix"])
    print("Total killed:", res["killed_total"])


def main():
    mA = 400_000
    mD = 400_000
    tierA = 12
    tierD = 12

    # FULL rally attackers: 1 of each type
    attackers = [
        make_att("Infantry", tierA, mA),
        make_att("Ranged", tierA, mA),
        make_att("Cavalry", tierA, mA),
    ]

    # SOLO reinforcement: pick Infantry defender (different from some attackers)
    defenders = [make_def("Infantry", tierD, mD)]

    res = compute_battle_like_sheet(
        attackers=[make_att("Cavalry", tierA, mA)],  # SOLO
        defenders=[
            make_def("Infantry", tierD, mD),
            make_def("Ranged", tierD, mD),
            make_def("Cavalry", tierD, mD),
        ],
        scenario="solo_vs_fullrein",
    )

    pretty_print("solo_vs_fullrein (solo vs full rein)", res)


if __name__ == "__main__":
    main()
