import streamlit as st

st.set_page_config(
    page_title="GOTC Calculators",)

st.write("# Welcome to the GOTC Calculators page!")

st.sidebar.success("Select a calculator above.")

st.markdown("""
This page hosts various calculators to help you optimize your gameplay in GOTC. Select a calculator available from the sidebar.

            Calculators currently available:

            - Dragon vs Dragon Calculator: Estimate damage and healing costs in dragon duels.

            - Stats Calculator: similar to the old GOTC Tips PVP Calculator, the Stats Calculator calculates \n
            your "true stats" on PVP occasions and also compares to theoretical maxed stats for your troop type.

            Soon:
            - Battle Simulator: Simulate battles between attackers and defenders.

            - March Time Calculator: Calculates march times for your troops given your \n 
            troop type/tier/speed buffs and origin/destination coordinates.


            Questions or suggestions? Message me on Discord (Lipeeeee).

            """)