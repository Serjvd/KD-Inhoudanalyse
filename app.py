import streamlit as st
import tempfile
import os
import pandas as pd

from inhoudsanalyse import vergelijk_werkprocessen
from comparator import vergelijk_kds

st.set_page_config(page_title="Kwalificatiedossier Analyse", layout="wide")
st.title("📚 Kwalificatiedossier Analyse Tool")

# Initialiseer session_state voor uploads
for key in ["oud_pdf", "nieuw_pdf"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Tabs voor twee functies
tabs = st.tabs(["🔍 Vergelijk op kerntaakniveau", "🧠 Inhoudelijke werkprocesanalyse"])

# --- TAB 1: KDvergelijker2 --- #
with tabs[0]:
    st.header("🔍 Globale vergelijking van twee kwalificatiedossiers (kerntaakniveau)")
    st.markdown("Vergelijkt teksten van volledige kerntaken (geen werkprocessen).")

    col1, col2 = st.columns(2)
    with col1:
        oud_pdf = st.file_uploader("⬅️ Oud dossier (PDF)", type="pdf", key="upload_oud")
        if oud_pdf:
            st.session_state["oud_pdf"] = oud_pdf
    with col2:
        nieuw_pdf = st.file_uploader("➡️ Nieuw dossier (PDF)", type="pdf", key="upload_nieuw")
        if nieuw_pdf:
            st.session_state["nieuw_pdf"] = nieuw_pdf

    oud_pdf = st.session_state["oud_pdf"]
    nieuw_pdf = st.session_state["nieuw_pdf"]

    if oud_pdf and nieuw_pdf:
        st.write("Bestanden geüpload, vergelijking start...")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp1:
                tmp1.write(oud_pdf.read())
                oud_path = tmp1.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp2:
                tmp2.write(nieuw_pdf.read())
                nieuw_path = tmp2.name

            result_df, excel_path = vergelijk_kds(oud_path, nieuw_path)
            st.success("✅ Vergelijking voltooid")
            st.dataframe(result_df)

            with open(excel_path, "rb") as f:
                st.download_button(
                    label="📥 Download Excel (kerntaakvergelijking)",
                    data=f,
                    file_name="kd_kerntaak_vergelijking.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Fout bij vergelijken: {e}")

# --- TAB 2: Inhoudsanalyse (werkprocessen) --- #
with tabs[1]:
    st.header("🧠 Inhoudelijke vergelijking op werkprocesniveau")
    st.markdown("Vergelijkt werkprocessen inhoudelijk (semantisch, inclusief impactscore).")

    oud_pdf = st.session_state["oud_pdf"]
    nieuw_pdf = st.session_state["nieuw_pdf"]

    if oud_pdf and nieuw_pdf:
        st.write("Bestanden geüpload, werkproces-analyse start...")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp1:
                tmp1.write(oud_pdf.read())
                oud_path = tmp1.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp2:
                tmp2.write(nieuw_pdf.read())
                nieuw_path = tmp2.name

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
            st.error(f"Fout bij inhoudsanalyse: {e}")
    else:
        st.info("📂 Upload eerst beide PDF-bestanden in de eerste tab om de analyse te starten.")
