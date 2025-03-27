import streamlit as st
import tempfile
import os
import pandas as pd
import traceback
from inhoudsanalyse import vergelijk_werkprocessen
from comparator import vergelijk_kds

st.set_page_config(page_title="Kwalificatiedossier Analyse", layout="wide")
st.title("📚 Kwalificatiedossier Analyse Tool")

# Tabs voor beide functies
tabs = st.tabs(["🔍 Vergelijk op kerntaakniveau", "🧠 Inhoudelijke werkprocesanalyse"])

# --- Gedeelde uploadfunctionaliteit boven de tabs ---
col1, col2 = st.columns(2)
with col1:
    oud_pdf = st.file_uploader("⬅️ Oud dossier (PDF)", type="pdf", key="upload_oud")
with col2:
    nieuw_pdf = st.file_uploader("➡️ Nieuw dossier (PDF)", type="pdf", key="upload_nieuw")

# --- TAB 1: Kerntaakvergelijking --- #
with tabs[0]:
    st.header("🔍 Globale vergelijking van twee kwalificatiedossiers (kerntaakniveau)")
    st.markdown("Vergelijkt teksten van volledige kerntaken (geen werkprocessen).")

    if oud_pdf and nieuw_pdf:
        st.write("Bestanden geüpload, vergelijking start...")

        try:
            # Veilige tijdelijke opslag
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as tmp1:
                tmp1.write(oud_pdf.read())
                tmp1.flush()
                os.fsync(tmp1.fileno())
                oud_path = tmp1.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as tmp2:
                tmp2.write(nieuw_pdf.read())
                tmp2.flush()
                os.fsync(tmp2.fileno())
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
        except Exception:
            st.error("Er is iets misgegaan bij de kerntaakanalyse.")
            st.code(traceback.format_exc(), language="python")
        finally:
            for path in ["oud_path", "nieuw_path"]:
                try:
                    if path in locals():
                        os.unlink(locals()[path])
                except Exception:
                    pass

# --- TAB 2: Werkprocesanalyse --- #
with tabs[1]:
    st.header("🧠 Inhoudelijke vergelijking op werkprocesniveau")
    st.markdown("Vergelijkt werkprocessen inhoudelijk (semantisch, inclusief impactscore).")

    if oud_pdf and nieuw_pdf:
        st.write("Bestanden geüpload, werkproces-analyse start...")

        try:
            # Veilige tijdelijke opslag
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as tmp1:
                tmp1.write(oud_pdf.read())
                tmp1.flush()
                os.fsync(tmp1.fileno())
                oud_path = tmp1.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as tmp2:
                tmp2.write(nieuw_pdf.read())
                tmp2.flush()
                os.fsync(tmp2.fileno())
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
                    mime
