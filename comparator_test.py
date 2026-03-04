from calculator import statsComparator

def main():
    troop_type = "Cavalry"

    # Attacker-only inputs
    attacker = {
        "baseatkbuff": 1305.16,
        "marcheratkbuff": 6873.38,
        "atkvscav": 1544.42,
        "atkvsinf": 1097.48,
        "atkvsrng": 346.15,
    }

    # Defender-only inputs
    defender = {
        "basedefbuff": 1018.42,
        "basehealthbuff": 365.07,
        "defatsopbuff": 2600.58,
        "healthatsopbuff": 2108.68,
        "defvscav": 844.55,
        "defvsinf": 589.85,
        "defvsrng": 557.12,
        "defdefensebuff": 86.00,
        "defhealthbuff": 96.41,
    }

    out = statsComparator(troop_type, attacker, defender)

    print("\n=== Attacker true power totals ===")
    print(out["attacker_true_power"])

    print("\n=== Defender true power totals ===")
    print(out["defender_true_power"])

    print("\n=== Attacker vs Maxed (Attack metrics) ===")
    for k, v in out["comparison"]["attacker_vs_maxed"].items():
        print(k, "=>", v)

    print("\n=== Defender vs Maxed (Defense/Health metrics) ===")
    for k, v in out["comparison"]["defender_vs_maxed"].items():
        print(k, "=>", v)

if __name__ == "__main__":
    main()
