import streamlit as st
import pandas as pd
import tempfile
import os
from inhoudsanalyse import vergelijk_werkprocessen

def main():
    st.set_page_config(page_title="Kwalificatiedossier vergelijker op inhoud", layout="wide")
    st.title("📄 Vergelijk inhoud van kwalificatiedossiers")

    st.markdown("""
        Upload hieronder een oud en een nieuw kwalificatiedossier in PDF-formaat.
        De applicatie vergelijkt werkprocessen inhoudelijk en genereert een Excelrapport met:
        - codes en namen
        - tekstverschillen
        - impactscore
        - inhoudelijke analyse
        - samenvatting per kerntaak
    """)

    col1, col2 = st.columns(2)
    with col1:
        oud_pdf = st.file_uploader("⬅️ Oud dossier (PDF)", type="pdf", key="oud")
    with col2:
        nieuw_pdf = st.file_uploader("➡️ Nieuw dossier (PDF)", type="pdf", key="nieuw")

    if oud_pdf and nieuw_pdf:
        st.write("Bestanden geüpload, nu beginnen met analyse...")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp1:
                tmp1.write(oud_pdf.read())
                oud_path = tmp1.name
            st.write("Oud bestand opgeslagen:", oud_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp2:
                tmp2.write(nieuw_pdf.read())
                nieuw_path = tmp2.name
            st.write("Nieuw bestand opgeslagen:", nieuw_path)

            df, samenvatting, excel_path = vergelijk_werkprocessen(oud_path, nieuw_path)
            st.success("✅ Analyse voltooid")

            st.subheader("📋 Gedetailleerde vergelijking per werkproces")
            st.dataframe(df)

            st.subheader("🧾 Samenvatting per kerntaak")
            st.dataframe(samenvatting)

            with open(excel_path, "rb") as f:
                st.download_button(
                    label="📥 Download Excelrapport (2 tabbladen)",
                    data=f,
                    file_name="vergelijking_resultaat.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Er is iets misgegaan: {e}")

if __name__ == "__main__":
    main()
