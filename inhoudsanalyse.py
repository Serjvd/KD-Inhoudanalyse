import pdfplumber
import re
import pandas as pd
from fuzzywuzzy import fuzz
from typing import List, Tuple

def extract_full_text(pdf_path: str) -> str:
    """Extraheert alle tekst uit het PDF-bestand."""
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def extract_werkprocesblokken(text: str) -> dict:
    """Extraheert werkprocesblokken uit het tekstbestand."""
    pattern = r"(B\d+-K\d+-W\d+):\s+([^\n]+)"
    blokken = {}
    matches = list(re.finditer(pattern, text))

    for i, match in enumerate(matches):
        code = match.group(1)
        naam = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blokken[code] = {
            "naam": naam,
            "tekst": text[start:end].strip()
        }
    return blokken

def inhoudelijk_verschil(oud: List[str], nieuw: List[str], drempel: int = 85) -> List[int]:
    """Vergelijkt de inhoud van twee lijsten tekstregels met fuzzy matching."""
    scores = []
    for nieuw_zin in nieuw:
        hoogste = 0
        for oud_zin in oud:
            score = fuzz.ratio(nieuw_zin, oud_zin)
            hoogste = max(hoogste, score)
        scores.append(hoogste)
    return scores

def vergelijk_werkprocessen(oud_pdf: str, nieuw_pdf: str) -> pd.DataFrame:
    """Vergelijkt werkprocessen tussen een oud en nieuw kwalificatiedossier en genereert een DataFrame."""
    oud_text = extract_full_text(oud_pdf)
    nieuw_text = extract_full_text(nieuw_pdf)

    oud_blokken = extract_werkprocesblokken(oud_text)
    nieuw_blokken = extract_werkprocesblokken(nieuw_text)

    resultaten = []
    alle_codes = sorted(set(oud_blokken.keys()) | set(nieuw_blokken.keys()))

    for code in alle_codes:
        oud = oud_blokken.get(code, {})
        nieuw = nieuw_blokken.get(code, {})

        naam = nieuw.get("naam") or oud.get("naam") or ""
        oud_tekst = oud.get("tekst", "").strip()
        nieuw_tekst = nieuw.get("tekst", "").strip()

        # Verplaatsing detecteren: zelfde naam, andere code
        if oud.get("naam") == nieuw.get("naam") and oud != nieuw:
            impact = "Verplaatst"
            score = "Weinig impact"
            analyse = f"Werkproces is verplaatst van code {code} naar nieuwe code"
        elif oud_tekst == nieuw_tekst:
            impact = "Geen"
            score = "Geen impact"
            analyse = "Tekst is identiek"
        elif not oud_tekst:
            impact = "Toegevoegd"
            score = "Impact"
            analyse = "Nieuw werkproces in het nieuwe dossier"
        elif not nieuw_tekst:
            impact = "Verwijderd"
            score = "Impact"
            analyse = "Werkproces is verwijderd in het nieuwe dossier"
        else:
            scores = inhoudelijk_verschil(oud_tekst.splitlines(), nieuw_tekst.splitlines())
            gemiddelde = sum(scores) / len(scores) if scores else 100
            if gemiddelde > 90:
                score = "Geen impact"
            elif gemiddelde > 75:
                score = "Weinig impact"
            elif gemiddelde > 60:
                score = "Impact"
            else:
                score = "Hoge impact"
            impact = "Gewijzigd"
            analyse = f"Inhoudelijke wijziging gedetecteerd (gemiddelde gelijkenis: {gemiddelde:.0f}%)"

        resultaten.append({
            "Code": code,
            "Naam": naam,
            "Oude tekst": oud_tekst,
            "Nieuwe tekst": nieuw_tekst,
            "Impact": impact,
            "Impactscore": score,
            "Analyse": analyse
        })

    return pd.DataFrame(resultaten)
