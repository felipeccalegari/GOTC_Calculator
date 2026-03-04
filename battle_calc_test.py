from calculator import compute_player_outputs
from models import attackBattleStats, defenseBattleStats

attacker = attackBattleStats.from_dict({
    "TroopType": "inf",
    "TroopTier": 12,
    "baseAttackBuff": 900.0,
    "marcherAttackBuff": 6500.0,
    "attvscav": 1400.0,
    "attvsinf": 900.0,
    "attvsrng": 360.0,
    "msizeAtt": 400000
})

defender1 = defenseBattleStats.from_dict({
    "TroopType": "inf",
    "TroopTier": 12,
    "msizeDef": 400000,
    "baseDefenseBuff": 900.0,
    "baseHealthBuff": 300.0,
    "defenseatsopBuff": 2200.0,
    "healthatsopBuff": 2100.0,
    "defvscav": 800.0,
    "defvsinf": 500.0,
    "defvsrng": 520.0,
    "defenderdefensebuff": 86.0,
    "defenderhealthbuff": 96.0
})

compute_player_outputs(attacker, defender1)
print("Inf killed: ", compute_player_outputs(attacker, defender1)["Infantry Killed"])
print("Cav killed: ", compute_player_outputs(attacker, defender1)["Cavalry Killed"])
print("Rng killed: ", compute_player_outputs(attacker, defender1)["Ranged Killed"])
print("Total killed: ", compute_player_outputs(attacker, defender1)["Total Killed"])