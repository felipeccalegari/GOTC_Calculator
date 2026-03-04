# streamlit_battle.py
import streamlit as st
import pandas as pd

from models import TroopType, attackBattleStats, defenseBattleStats
from calculator import compute_battle_like_sheet

st.set_page_config(page_title="Battle Simulator", page_icon="⚔️")
st.title("Battle Simulator ⚔️")

# =========================
# Helpers (minimal additions)
# =========================

TT_MAP = {
    "Infantry": TroopType.INFANTRY,
    "Ranged": TroopType.RANGED,
    "Cavalry": TroopType.CAVALRY,
}

def _build_att(tt_str, tier, msize, baseAtk, marcherAtk, vsCav, vsInf, vsRng):
    return attackBattleStats(
        TroopType=TT_MAP[tt_str],
        TroopTier=int(tier),
        msizeAtt=int(msize),
        baseAttackBuff=float(baseAtk),
        marcherAttackBuff=float(marcherAtk),
        attvscav=float(vsCav),
        attvsinf=float(vsInf),
        attvsrng=float(vsRng),
    )

def _build_def(tt_str, tier, msize, baseDef, baseHp, defAtSop, hpAtSop, vsCav, vsInf, vsRng, defDefBuff, defHpBuff):
    return defenseBattleStats(
        TroopType=TT_MAP[tt_str],
        TroopTier=int(tier),
        msizeDef=int(msize),
        baseDefenseBuff=float(baseDef),
        baseHealthBuff=float(baseHp),
        defenseatsopBuff=float(defAtSop),
        healthatsopBuff=float(hpAtSop),
        defvscav=float(vsCav),
        defvsinf=float(vsInf),
        defvsrng=float(vsRng),
        defenderdefensebuff=float(defDefBuff),
        defenderhealthbuff=float(defHpBuff),
    )

def dfs_from_battle_result(res: dict):
    # Attackers table
    df_attackers = pd.DataFrame(res.get("attackers", []))
    if not df_attackers.empty:
        cols = ["TroopType", "Tier", "MarchSize", "Att_vs_Inf", "Att_vs_Cav", "Att_vs_Ranged"]
        df_attackers = df_attackers[[c for c in cols if c in df_attackers.columns]]

    # Defenders table
    df_defenders = pd.DataFrame(res.get("defenders", []))
    if not df_defenders.empty:
        cols = ["TroopType", "Tier", "MarchSize", "TotalHealth",
                "TotalDef_vs_Inf", "TotalDef_vs_Cav", "TotalDef_vs_Ranged"]
        df_defenders = df_defenders[[c for c in cols if c in df_defenders.columns]]

    # Kills matrix
    killed_matrix = res.get("killed_matrix", {})
    df_matrix = pd.DataFrame.from_dict(killed_matrix, orient="index").fillna(0).astype(int)

    wanted_cols = ["Infantry", "Cavalry", "Ranged"]
    df_matrix = df_matrix[[c for c in wanted_cols if c in df_matrix.columns]]

    df_matrix["Row Total"] = df_matrix.sum(axis=1)
    col_total = df_matrix.sum(axis=0).to_frame().T
    col_total.index = ["Col Total"]
    df_matrix = pd.concat([df_matrix, col_total], axis=0)

    # Totals breakdown
    by_att = res.get("killed_by_attacker_type", {})
    by_def = res.get("killed_by_defender_type", {})
    total = res.get("killed_total", 0)

    rows = []
    for k, v in by_att.items():
        rows.append({"Group": "Killed by attacker type", "Type": k, "Killed": int(v)})
    for k, v in by_def.items():
        rows.append({"Group": "Killed by defender type", "Type": k, "Killed": int(v)})

    rows.append({"Group": "Grand total", "Type": "-", "Killed": int(total)})
    df_totals = pd.DataFrame(rows)

    return df_attackers, df_defenders, df_matrix, df_totals


def _render_result(res: dict):
    df_attackers, df_defenders, df_matrix, df_totals = dfs_from_battle_result(res)

    st.subheader("Attackers (effective attack vs troop types)")
    st.dataframe(df_attackers, use_container_width=True)

    st.subheader("Defenders (total health + total defense vs troop types)")
    st.dataframe(df_defenders, use_container_width=True)

    st.subheader("Kills Matrix (attacker rows x defender columns)")
    st.dataframe(df_matrix, use_container_width=True)

    st.subheader("Totals")
    st.dataframe(df_totals, use_container_width=True)


# =========================
# UI Scenarios
# =========================

battle_formats = [
    "Rally vs Solo Reinforcements",
    "Solo vs Multi-Reinforcements",
    "Rally vs Multi-Reinforcements"
]
choice = st.selectbox("Select Battle Format", options=battle_formats, key="battle_format_choice")


def battle_rally_vs_solo():
    st.write("Rally vs Solo Reinforcements")
    with st.form(key="battle_rally_simulator_form"):
        rallysize = st.number_input("Rally Size", min_value=1, value=2000000, key="rallysize")

        atkCav, atkInf, atkRng, defender = st.columns(4)

        with atkCav:
            st.write("### Cavalry Attacker Stats")
            troopTypeAttCav = st.selectbox("Troop Type", options=["Cavalry"], key="troopTypeAttCav")
            tierAttCav = st.selectbox("Troop Tier", options=[11, 12], key="tierAttCav")
            msizeAttCav = st.number_input("Percentage of Cavalry (DON'T insert % symbol)", min_value=1, value=40, key="msizeAttCav")

            st.write("#### Cavalry March Size: " + str(int(msizeAttCav)))
            baseAttTroopTypeBuffAttCav = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1500.0, key="baseTroopTypeBuffAttCav")
            marcherTroopBuffAttCav = st.number_input("Marcher Troop Attack Buff", min_value=0.0, value=6500.0, key="marcherTroopBuffAttCav")
            atkVsCavAttCav = st.number_input("Attack vs Cavalry", min_value=0.0, value=500.0, key="atkVsCavAttCav")
            atkVsInfAttCav = st.number_input("Attack vs Infantry", min_value=0.0, value=400.0, key="atkVsInfAttCav")
            atkVsRngAttCav = st.number_input("Attack vs Ranged", min_value=0.0, value=300.0, key="atkVsRngAttCav")

        with atkInf:
            st.write("### Infantry Attacker Stats")
            troopTypeAttInf = st.selectbox("Troop Type", options=["Infantry"], key="troopTypeAttInf")
            tierAttInf = st.selectbox("Troop Tier", options=[11, 12], key="tierAttInf")
            msizeAttInf = st.number_input("Percentage of Infantry (DON'T insert % symbol)", min_value=1, value=30, key="msizeAttInf")

            st.write("#### Infantry March Size: " + str(int(msizeAttInf)))
            baseAttTroopTypeBuffAttInf = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1500.0, key="baseTroopTypeBuffAttInf")
            marcherTroopBuffAttInf = st.number_input("Marcher Troop Attack Buff", min_value=0.0, value=6500.0, key="marcherTroopBuffAttInf")
            atkVsCavAttInf = st.number_input("Attack vs Cavalry", min_value=0.0, value=500.0, key="atkVsCavAttInf")
            atkVsInfAttInf = st.number_input("Attack vs Infantry", min_value=0.0, value=400.0, key="atkVsInfAttInf")
            atkVsRngAttInf = st.number_input("Attack vs Ranged", min_value=0.0, value=300.0, key="atkVsRngAttInf")

        with atkRng:
            st.write("### Ranged Attacker Stats")
            troopTypeAttRng = st.selectbox("Troop Type", options=["Ranged"], key="troopTypeAttRng")
            tierAttRng = st.selectbox("Troop Tier", options=[11, 12], key="tierAttRng")
            msizeAttRng = st.number_input("Percentage of Ranged (DON'T insert % symbol)", min_value=1, value=30, key="msizeAttRng")
            st.write("#### Ranged March Size: " + str(int(msizeAttRng)))
            baseAttTroopTypeBuffAttRng = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1500.0, key="baseTroopTypeBuffAttRng")
            marcherTroopBuffAttRng = st.number_input("Marcher Troop Attack Buff", min_value=0.0, value=6500.0, key="marcherTroopBuffAttRng")
            atkVsCavAttRng = st.number_input("Attack vs Cavalry", min_value=0.0, value=500.0, key="atkVsCavAttRng")
            atkVsInfAttRng = st.number_input("Attack vs Infantry", min_value=0.0, value=400.0, key="atkVsInfAttRng")
            atkVsRngAttRng = st.number_input("Attack vs Ranged", min_value=0.0, value=300.0, key="atkVsRngAttRng")

        with defender:
            st.write("### Defender Stats")
            troopTypeDef = st.selectbox("Troop Type", options=["Infantry", "Ranged", "Cavalry"], key="troopTypeDefRally")
            tierDef = st.selectbox("Troop Tier", options=[11, 12], key="tierDefRally")
            msizeDef = st.number_input("March Size", min_value=1, value=100000, key="msizeDefRally")
            baseDefTroopTypeBuffDef = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1000.0, key="baseDefTroopTypeBuffDefRally")
            baseHealthTroopBuffDef = st.number_input("Base Troop Health Buff", min_value=0.0, value=300.0, key="baseHealthTroopBuffDefRally")
            defenseatsopBuffDef = st.number_input("Defense at SOP Buff", min_value=0.0, value=2000.0, key="defenseatsopBuffDefRally")
            healthatsopBuffDef = st.number_input("Health at SOP Buff", min_value=0.0, value=2000.0, key="healthatsopBuffDefRally")
            defVsCavDef = st.number_input("Defense vs Cavalry", min_value=0.0, value=800.0, key="defVsCavDefRally")
            defVsInfDef = st.number_input("Defense vs Infantry", min_value=0.0, value=600.0, key="defVsInfDefRally")
            defVsRngDef = st.number_input("Defense vs Ranged", min_value=0.0, value=500.0, key="defVsRngDefRally")
            defenderdefenseBuffDef = st.number_input("Defender Defense Buff", min_value=0.0, value=2000.0, key="defenderdefenseBuffDefRally")
            defenderhealthBuffDef = st.number_input("Defender Health Buff", min_value=0.0, value=2100.0, key="defenderhealthBuffDefRally")

        submitted = st.form_submit_button("Simulate Battle")

    if submitted:
        attackers = [
            _build_att("Cavalry", tierAttCav, msizeAttCav, baseAttTroopTypeBuffAttCav, marcherTroopBuffAttCav,
                       atkVsCavAttCav, atkVsInfAttCav, atkVsRngAttCav),
            _build_att("Infantry", tierAttInf, msizeAttInf, baseAttTroopTypeBuffAttInf, marcherTroopBuffAttInf,
                       atkVsCavAttInf, atkVsInfAttInf, atkVsRngAttInf),
            _build_att("Ranged", tierAttRng, msizeAttRng, baseAttTroopTypeBuffAttRng, marcherTroopBuffAttRng,
                       atkVsCavAttRng, atkVsInfAttRng, atkVsRngAttRng),
        ]

        defenders = [
            _build_def(troopTypeDef, tierDef, msizeDef,
                       baseDefTroopTypeBuffDef, baseHealthTroopBuffDef,
                       defenseatsopBuffDef, healthatsopBuffDef,
                       defVsCavDef, defVsInfDef, defVsRngDef,
                       defenderdefenseBuffDef, defenderhealthBuffDef)
        ]

        res = compute_battle_like_sheet(attackers=attackers, defenders=defenders, scenario="fullrally_vs_solorein")
        _render_result(res)


def battle_solo_vs_multi():
    st.write("Solo vs Multi-Reinforcements")
    with st.form(key="battle_solo_multi_simulator_form"):
        attacker, infdef, rngdef, cavdef = st.columns(4)
        reincap = st.number_input("Reinforcement Capacity at SOP", min_value=1, value=1200000, key="reincap")

        with attacker:
            st.write("### Attacker Stats")
            troopTypeAtt = st.selectbox("Troop Type", options=["Infantry", "Ranged", "Cavalry"], key="troopTypeAttSoloMulti")
            tierAtt = st.selectbox("Troop Tier", options=[11, 12], key="tierAttSoloMulti")
            msizeAtt = st.number_input("March Size", min_value=1, value=400000, key="msizeAttSoloMulti")
            baseAttTroopTypeBuffAtt = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1390.0, key="baseTroopTypeBuffAttSoloMulti")
            marcherTroopBuffAtt = st.number_input("Marcher Troop Attack Buff", min_value=0.0, value=6873.0, key="marcherTroopBuffAttSoloMulti")
            atkVsCavAtt = st.number_input("Attack vs Cavalry", min_value=0.0, value=1610.0, key="atkVsCavAttSoloMulti")
            atkVsInfAtt = st.number_input("Attack vs Infantry", min_value=0.0, value=1097.0, key="atkVsInfAttSoloMulti")
            atkVsRngAtt = st.number_input("Attack vs Ranged", min_value=0.0, value=346.0, key="atkVsRngAttSoloMulti")

        with infdef:
            st.write("### Infantry Defender Stats")
            troopTypeDefInf = st.selectbox("Troop Type", options=["Infantry"], key="troopTypeDefInfSoloMulti")
            tierDefInf = st.selectbox("Troop Tier", options=[11, 12], key="tierDefInfSoloMulti")
            msizeDefInf = st.number_input("Percentage of Infantry (DON'T insert % symbol)", min_value=1, value=40, key="sizeDefInfSoloMulti")
            
            st.write("#### Infantry Defense March Size: " + str(int(msizeDefInf)))
            baseDefTroopTypeBuffDefInf = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1018.0, key="baseDefTroopTypeBuffDefInfSoloMulti")
            baseHealthTroopBuffDefInf = st.number_input("Base Troop Health Buff", min_value=0.0, value=365.0, key="baseHealthTroopBuffDefInfSoloMulti")
            defenseatsopBuffDefInf = st.number_input("Defense at SOP Buff", min_value=0.0, value=2600.0, key="defenseatsopBuffDefInfSoloMulti")
            healthatsopBuffDefInf = st.number_input("Health at SOP Buff", min_value=0.0, value=2108.0, key="healthatsopBuffDefInfSoloMulti")
            defVsCavDefInf = st.number_input("Defense vs Cavalry", min_value=0.0, value=919.0, key="defVsCavDefInfSoloMulti")
            defVsInfDefInf = st.number_input("Defense vs Infantry", min_value=0.0, value=589.0, key="defVsInfDefInfSoloMulti")
            defVsRngDefInf = st.number_input("Defense vs Ranged", min_value=0.0, value=608.0, key="defVsRngDefInfSoloMulti")
            defenderdefenseBuffDefInf = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefInfSoloMulti")
            defenderhealthBuffDefInf = st.number_input("Defender Health Buff", min_value=0.0, value=96.0, key="defenderhealthBuffDefInfSoloMulti")

        with rngdef:
            st.write("### Ranged Defender Stats")
            troopTypeDefRng = st.selectbox("Troop Type", options=["Ranged"], key="troopTypeDefRngSoloMulti")
            tierDefRng = st.selectbox("Troop Tier", options=[11, 12], key="tierDefRngSoloMulti")
            msizeDefRng = st.number_input("Percentage of Ranged (DON'T insert % symbol)", min_value=1, value=30, key="sizeDefRngSoloMulti")
            st.write("#### Ranged Defense March Size: " + str(int(msizeDefRng)))
            baseDefTroopTypeBuffDefRng = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1225.0, key="baseDefTroopTypeBuffDefRngSoloMulti")
            baseHealthTroopBuffDefRng = st.number_input("Base Troop Health Buff", min_value=0.0, value=438.0, key="baseHealthTroopBuffDefRngSoloMulti")
            defenseatsopBuffDefRng = st.number_input("Defense at SOP Buff", min_value=0.0, value=2720.0, key="defenseatsopBuffDefRngSoloMulti")
            healthatsopBuffDefRng = st.number_input("Health at SOP Buff", min_value=0.0, value=2302.0, key="healthatsopBuffDefRngSoloMulti")
            defVsCavDefRng = st.number_input("Defense vs Cavalry", min_value=0.0, value=838.0, key="defVsCavDefRngSoloMulti")
            defVsInfDefRng = st.number_input("Defense vs Infantry", min_value=0.0, value=989.0, key="defVsInfDefRngSoloMulti")
            defVsRngDefRng = st.number_input("Defense vs Ranged", min_value=0.0, value=477.0, key="defVsRngDefRngSoloMulti")
            defenderdefenseBuffDefRng = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefRngSoloMulti")
            defenderhealthBuffDefRng = st.number_input("Defender Health Buff", min_value=0.0, value=87.0, key="defenderhealthBuffDefRngSoloMulti")

        with cavdef:
            st.write("### Cavalry Defender Stats")
            troopTypeDefCav = st.selectbox("Troop Type", options=["Cavalry"], key="troopTypeDefCavSoloMulti")
            tierDefCav = st.selectbox("Troop Tier", options=[11, 12], key="tierDefCavSoloMulti")
            msizeDefCav = st.number_input("Percentage of Cavalry (DON'T insert % symbol)", min_value=1, value=30, key="sizeDefCavSoloMulti")
            st.write("#### Cavalry Defense March Size: " + str(int(msizeDefCav)))
            baseDefTroopTypeBuffDefCav = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1197.0, key="baseDefTroopTypeBuffDefCavSoloMulti")
            baseHealthTroopBuffDefCav = st.number_input("Base Troop Health Buff", min_value=0.0, value=337.0, key="baseHealthTroopBuffDefCavSoloMulti")
            defenseatsopBuffDefCav = st.number_input("Defense at SOP Buff", min_value=0.0, value=2310.0, key="defenseatsopBuffDefCavSoloMulti")
            healthatsopBuffDefCav = st.number_input("Health at SOP Buff", min_value=0.0, value=2873.0, key="healthatsopBuffDefCavSoloMulti")
            defVsCavDefCav = st.number_input("Defense vs Cavalry", min_value=0.0, value=521.0, key="defVsCavDefCavSoloMulti")
            defVsInfDefCav = st.number_input("Defense vs Infantry", min_value=0.0, value=1094.0, key="defVsInfDefCavSoloMulti")
            defVsRngDefCav = st.number_input("Defense vs Ranged", min_value=0.0, value=917.0, key="defVsRngDefCavSoloMulti")
            defenderdefenseBuffDefCav = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefCavSoloMulti")
            defenderhealthBuffDefCav = st.number_input("Defender Health Buff", min_value=0.0, value=45.0, key="defenderhealthBuffDefCavSoloMulti")

        submitted = st.form_submit_button("Simulate Battle")

    if submitted:
        attackers = [
            _build_att(troopTypeAtt, tierAtt, msizeAtt, baseAttTroopTypeBuffAtt, marcherTroopBuffAtt,
                       atkVsCavAtt, atkVsInfAtt, atkVsRngAtt)
        ]
        defenders = [
            _build_def("Infantry", tierDefInf, msizeDefInf,
                       baseDefTroopTypeBuffDefInf, baseHealthTroopBuffDefInf,
                       defenseatsopBuffDefInf, healthatsopBuffDefInf,
                       defVsCavDefInf, defVsInfDefInf, defVsRngDefInf,
                       defenderdefenseBuffDefInf, defenderhealthBuffDefInf),

            _build_def("Ranged", tierDefRng, msizeDefRng,
                       baseDefTroopTypeBuffDefRng, baseHealthTroopBuffDefRng,
                       defenseatsopBuffDefRng, healthatsopBuffDefRng,
                       defVsCavDefRng, defVsInfDefRng, defVsRngDefRng,
                       defenderdefenseBuffDefRng, defenderhealthBuffDefRng),

            _build_def("Cavalry", tierDefCav, msizeDefCav,
                       baseDefTroopTypeBuffDefCav, baseHealthTroopBuffDefCav,
                       defenseatsopBuffDefCav, healthatsopBuffDefCav,
                       defVsCavDefCav, defVsInfDefCav, defVsRngDefCav,
                       defenderdefenseBuffDefCav, defenderhealthBuffDefCav),
        ]

        res = compute_battle_like_sheet(attackers=attackers, defenders=defenders, scenario="solo_vs_fullrein")
        _render_result(res)


def battle_rally_vs_multi():
    st.write("Rally vs Multi-Reinforcements")
    with st.form(key="battle_rally_multi_simulator_form"):
        rallysize = st.number_input("Rally Size", min_value=1, value=2000000, key="rallysize_multi")
        reincap = st.number_input("Reinforcement Capacity at SOP", min_value=1, value=100000, key="reincap_multi")

        atkCav, atkInf, atkRng, infdef, rngdef, cavdef = st.columns(6)

        with atkCav:
            st.write("### Cavalry Attacker Stats")
            troopTypeAttCav = st.selectbox("Troop Type", options=["Cavalry"], key="troopTypeAttCav_multi")
            tierAttCav = st.selectbox("Troop Tier", options=[11, 12], key="tierAttCav_multi")
            msizeAttCav = st.number_input("March Size", min_value=1, value=400000, key="msizeAttCav_multi")

            baseAttTroopTypeBuffAttCav = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1317.48, key="baseAttTroopTypeBuffAttCav_multi")
            marcherTroopBuffAttCav = st.number_input("Marcher Troop Attack Buff", min_value=0.0, value=7271.58, key="marcherTroopBuffAttCav_multi")
            atkVsCavAttCav = st.number_input("Attack vs Cavalry", min_value=0.0, value=1620.69, key="atkVsCavAttCav_multi")
            atkVsInfAttCav = st.number_input("Attack vs Infantry", min_value=0.0, value=471.49, key="atkVsInfAttCav_multi")
            atkVsRngAttCav = st.number_input("Attack vs Ranged", min_value=0.0, value=1642.80, key="atkVsRngAttCav_multi")

        with atkInf:
            st.write("### Infantry Attacker Stats")
            troopTypeAttInf = st.selectbox("Troop Type", options=["Infantry"], key="troopTypeAttInf_multi")
            tierAttInf = st.selectbox("Troop Tier", options=[11, 12], key="tierAttInf_multi")
            msizeAttInf = st.number_input("March Size", min_value=1, value=400000, key="msizeAttInf_multi")

            baseAttTroopTypeBuffAttInf = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1390.35, key="baseAttTroopTypeBuffAttInf_multi")
            marcherTroopBuffAttInf = st.number_input("Marcher Troop Attack Buff", min_value=0.0, value=6873.38, key="marcherTroopBuffAttInf_multi")
            atkVsCavAttInf = st.number_input("Attack vs Cavalry", min_value=0.0, value=1610.51, key="atkVsCavAttInf_multi")
            atkVsInfAttInf = st.number_input("Attack vs Infantry", min_value=0.0, value=1097.48, key="atkVsInfAttInf_multi")
            atkVsRngAttInf = st.number_input("Attack vs Ranged", min_value=0.0, value=346.15, key="atkVsRngAttInf_multi")

        with atkRng:
            st.write("### Ranged Attacker Stats")
            troopTypeAttRng = st.selectbox("Troop Type", options=["Ranged"], key="troopTypeAttRng_multi")
            tierAttRng = st.selectbox("Troop Tier", options=[11, 12], key="tierAttRng_multi")
            msizeAttRng = st.number_input("March Size", min_value=1, value=400000, key="msizeAttRng_multi")

            baseAttTroopTypeBuffAttRng = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1308.81, key="baseAttTroopTypeBuffAttRng_multi")
            marcherTroopBuffAttRng = st.number_input("Marcher Troop Attack Buff", min_value=0.0, value=7415.18, key="marcherTroopBuffAttRng_multi")
            atkVsCavAttRng = st.number_input("Attack vs Cavalry", min_value=0.0, value=436.92, key="atkVsCavAttRng_multi")
            atkVsInfAttRng = st.number_input("Attack vs Infantry", min_value=0.0, value=1717.59, key="atkVsInfAttRng_multi")
            atkVsRngAttRng = st.number_input("Attack vs Ranged", min_value=0.0, value=1483.59, key="atkVsRngAttRng_multi")

        with infdef:
            st.write("### Infantry Defender Stats")
            troopTypeDefInf = st.selectbox("Troop Type", options=["Infantry"], key="troopTypeDefInf_multi")
            tierDefInf = st.selectbox("Troop Tier", options=[11, 12], key="tierDefInf_multi")
            msizeDefInf = st.number_input("March Size", min_value=1, value=400000, key="sizeDefInf_multi")

            baseDefTroopTypeBuffDefInf = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1018.42, key="baseDefTroopTypeBuffDefInf_multi")
            baseHealthTroopBuffDefInf = st.number_input("Base Troop Health Buff", min_value=0.0, value=365.07, key="baseHealthTroopBuffDefInf_multi")
            defenseatsopBuffDefInf = st.number_input("Defense at SOP Buff", min_value=0.0, value=2600.58, key="defenseatsopBuffDefInf_multi")
            healthatsopBuffDefInf = st.number_input("Health at SOP Buff", min_value=0.0, value=2108.68, key="healthatsopBuffDefInf_multi")
            defVsCavDefInf = st.number_input("Defense vs Cavalry", min_value=0.0, value=917.99, key="defVsCavDefInf_multi")
            defVsInfDefInf = st.number_input("Defense vs Infantry", min_value=0.0, value=589.85, key="defVsInfDefInf_multi")
            defVsRngDefInf = st.number_input("Defense vs Ranged", min_value=0.0, value=608.53, key="defVsRngDefInf_multi")
            defenderdefenseBuffDefInf = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefInf_multi")
            defenderhealthBuffDefInf = st.number_input("Defender Health Buff", min_value=0.0, value=96.41, key="defenderhealthBuffDefInf_multi")

        with rngdef:
            st.write("### Ranged Defender Stats")
            troopTypeDefRng = st.selectbox("Troop Type", options=["Ranged"], key="troopTypeDefRng_multi")
            tierDefRng = st.selectbox("Troop Tier", options=[11, 12], key="tierDefRng_multi")
            msizeDefRng = st.number_input("March Size", min_value=1, value=400000, key="sizeDefRng_multi")

            baseDefTroopTypeBuffDefRng = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1225.62, key="baseDefTroopTypeBuffDefRng_multi")
            baseHealthTroopBuffDefRng = st.number_input("Base Troop Health Buff", min_value=0.0, value=438.98, key="baseHealthTroopBuffDefRng_multi")
            defenseatsopBuffDefRng = st.number_input("Defense at SOP Buff", min_value=0.0, value=2720.27, key="defenseatsopBuffDefRng_multi")
            healthatsopBuffDefRng = st.number_input("Health at SOP Buff", min_value=0.0, value=2302.55, key="healthatsopBuffDefRng_multi")
            defVsCavDefRng = st.number_input("Defense vs Cavalry", min_value=0.0, value=838.02, key="defVsCavDefRng_multi")
            defVsInfDefRng = st.number_input("Defense vs Infantry", min_value=0.0, value=989.71, key="defVsInfDefRng_multi")
            defVsRngDefRng = st.number_input("Defense vs Ranged", min_value=0.0, value=477.20, key="defVsRngDefRng_multi")
            defenderdefenseBuffDefRng = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefRng_multi")
            defenderhealthBuffDefRng = st.number_input("Defender Health Buff", min_value=0.0, value=87.23, key="defenderhealthBuffDefRng_multi")

        with cavdef:
            st.write("### Cavalry Defender Stats")
            troopTypeDefCav = st.selectbox("Troop Type", options=["Cavalry"], key="troopTypeDefCav_multi")
            tierDefCav = st.selectbox("Troop Tier", options=[11, 12], key="tierDefCav_multi")
            msizeDefCav = st.number_input("March Size", min_value=1, value=400000, key="sizeDefCav_multi")

            baseDefTroopTypeBuffDefCav = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1197.68, key="baseDefTroopTypeBuffDefCav_multi")
            baseHealthTroopBuffDefCav = st.number_input("Base Troop Health Buff", min_value=0.0, value=337.45, key="baseHealthTroopBuffDefCav_multi")
            defenseatsopBuffDefCav = st.number_input("Defense at SOP Buff", min_value=0.0, value=2310.14, key="defenseatsopBuffDefCav_multi")
            healthatsopBuffDefCav = st.number_input("Health at SOP Buff", min_value=0.0, value=2873.64, key="healthatsopBuffDefCav_multi")
            defVsCavDefCav = st.number_input("Defense vs Cavalry", min_value=0.0, value=521.90, key="defVsCavDefCav_multi")
            defVsInfDefCav = st.number_input("Defense vs Infantry", min_value=0.0, value=1094.47, key="defVsInfDefCav_multi")
            defVsRngDefCav = st.number_input("Defense vs Ranged", min_value=0.0, value=917.15, key="defVsRngDefCav_multi")
            defenderdefenseBuffDefCav = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefCav_multi")
            defenderhealthBuffDefCav = st.number_input("Defender Health Buff", min_value=0.0, value=45.0, key="defenderhealthBuffDefCav_multi")

        submitted = st.form_submit_button("Simulate Battle")

    if submitted:
        attackers = [
            _build_att("Cavalry", tierAttCav, msizeAttCav, baseAttTroopTypeBuffAttCav, marcherTroopBuffAttCav,
                       atkVsCavAttCav, atkVsInfAttCav, atkVsRngAttCav),
            _build_att("Infantry", tierAttInf, msizeAttInf, baseAttTroopTypeBuffAttInf, marcherTroopBuffAttInf,
                       atkVsCavAttInf, atkVsInfAttInf, atkVsRngAttInf),
            _build_att("Ranged", tierAttRng, msizeAttRng, baseAttTroopTypeBuffAttRng, marcherTroopBuffAttRng,
                       atkVsCavAttRng, atkVsInfAttRng, atkVsRngAttRng),
        ]

        defenders = [
            _build_def("Infantry", tierDefInf, msizeDefInf,
                       baseDefTroopTypeBuffDefInf, baseHealthTroopBuffDefInf,
                       defenseatsopBuffDefInf, healthatsopBuffDefInf,
                       defVsCavDefInf, defVsInfDefInf, defVsRngDefInf,
                       defenderdefenseBuffDefInf, defenderhealthBuffDefInf),

            _build_def("Ranged", tierDefRng, msizeDefRng,
                       baseDefTroopTypeBuffDefRng, baseHealthTroopBuffDefRng,
                       defenseatsopBuffDefRng, healthatsopBuffDefRng,
                       defVsCavDefRng, defVsInfDefRng, defVsRngDefRng,
                       defenderdefenseBuffDefRng, defenderhealthBuffDefRng),

            _build_def("Cavalry", tierDefCav, msizeDefCav,
                       baseDefTroopTypeBuffDefCav, baseHealthTroopBuffDefCav,
                       defenseatsopBuffDefCav, healthatsopBuffDefCav,
                       defVsCavDefCav, defVsInfDefCav, defVsRngDefCav,
                       defenderdefenseBuffDefCav, defenderhealthBuffDefCav),
        ]

        res = compute_battle_like_sheet(attackers=attackers, defenders=defenders, scenario="fullrally_vs_fullrein")
        _render_result(res)


# =========================
# Router
# =========================

if choice == battle_formats[0]:
    battle_rally_vs_solo()
elif choice == battle_formats[1]:
    battle_solo_vs_multi()
elif choice == battle_formats[2]:
    battle_rally_vs_multi()
