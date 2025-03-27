import pdfplumber
import re
import pandas as pd
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

def extract_full_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        tekst = []
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            # Sla inhoudsopgave-achtige pagina's over
            if page_text.count("...") > 5 or re.search(r'\.{3,} *\d+', page_text):
                continue
            tekst.append(page_text)
        return "\n".join(tekst)

def bepaal_deel(code: str) -> str:
    if code.startswith("B"):
        return "Basisdeel"
    elif code.startswith("P"):
        return "Profieldeel"
    else:
        return "Algemeen"

def extract_werkprocesblokken(text: str) -> List[Dict]:
    pattern = r"(B\d+-K\d+-W\d+):\s*([^\n]+)"
    matches = list(re.finditer(pattern, text))

    blokken = []
    for i, match in enumerate(matches):
        code = match.group(1).strip()
        naam = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        tekst = text[start:end].strip()
        deel = bepaal_deel(code)
        blokken.append({
            "code": code,
            "kerntaak": "-".join(code.split("-")[:2]),
            "naam": naam,
            "tekst": tekst,
            "deel": deel
        })
    return blokken

def vergelijk_inhoud(tekst1: str, tekst2: str) -> float:
    emb1 = model.encode(tekst1, convert_to_tensor=True)
    emb2 = model.encode(tekst2, convert_to_tensor=True)
    return float(util.cos_sim(emb1, emb2))

def bepaal_impactscore(sim: float) -> Tuple[str, str]:
    if sim > 0.95:
        return "Geen", "Geen impact"
    elif sim > 0.85:
        return "Gewijzigd", "Weinig impact"
    elif sim > 0.65:
        return "Gewijzigd", "Impact"
    else:
        return "Gewijzigd", "Hoge impact"

def vergelijk_werkprocessen(oud_pdf: str, nieuw_pdf: str) -> pd.DataFrame:
    oud_text = extract_full_text(oud_pdf)
    nieuw_text = extract_full_text(nieuw_pdf)

    oud_blokken = extract_werkprocesblokken(oud_text)
    nieuw_blokken = extract_werkprocesblokken(nieuw_text)

    resultaten = []
    gebruikte_nieuwe = set()

    for oud in oud_blokken:
        beste_match = None
        hoogste_score = -1

        for i, nieuw in enumerate(nieuw_blokken):
            if i in gebruikte_nieuwe:
                continue
            score = vergelijk_inhoud(oud["tekst"], nieuw["tekst"])
            if score > hoogste_score:
                hoogste_score = score
                beste_match = nieuw
                beste_index = i

        if beste_match and hoogste_score > 0.6:
            impact, impactscore = bepaal_impactscore(hoogste_score)
            resultaten.append({
                "Kerntaak": oud["kerntaak"],
                "Deel": oud["deel"],
                "Oude code": oud["code"],
                "Nieuwe code": beste_match["code"],
                "Naam": oud["naam"],
                "Oude tekst": oud["tekst"],
                "Nieuwe tekst": beste_match["tekst"],
                "Impact": impact,
                "Impactscore": impactscore,
                "Analyse": f"Gemiddelde inhoudsovereenkomst: {hoogste_score:.2f}"
            })
            gebruikte_nieuwe.add(beste_index)
        else:
            resultaten.append({
                "Kerntaak": oud["kerntaak"],
                "Deel": oud["deel"],
                "Oude code": oud["code"],
                "Nieuwe code": "",
                "Naam": oud["naam"],
                "Oude tekst": oud["tekst"],
                "Nieuwe tekst": "",
                "Impact": "Verwijderd",
                "Impactscore": "Hoge impact",
                "Analyse": "Niet meer aanwezig in nieuwe dossier"
            })

    for i, nieuw in enumerate(nieuw_blokken):
        if i not in gebruikte_nieuwe:
            resultaten.append({
                "Kerntaak": nieuw["kerntaak"],
                "Deel": nieuw["deel"],
                "Oude code": "",
                "Nieuwe code": nieuw["code"],
                "Naam": nieuw["naam"],
                "Oude tekst": "",
                "Nieuwe tekst": nieuw["tekst"],
                "Impact": "Toegevoegd",
                "Impactscore": "Impact",
                "Analyse": "Nieuw werkproces in het nieuwe dossier"
            })

    df = pd.DataFrame(resultaten)

    # Samenvatting per kerntaak
    samenvatting = (
        df.groupby(["Kerntaak", "Deel"])
        .agg(
            Totaal=("Naam", "count"),
            Gewijzigd=("Impact", lambda x: (x == "Gewijzigd").sum()),
            Toegevoegd=("Impact", lambda x: (x == "Toegevoegd").sum()),
            Verwijderd=("Impact", lambda x: (x == "Verwijderd").sum()),
            Gem_Impactscore=("Impactscore", lambda x: x.map({
                "Geen impact": 0,
                "Weinig impact": 1,
                "Impact": 2,
                "Hoge impact": 3
            }).mean().round(2))
        )
        .reset_index()
    )

    # Schrijf naar Excel met 2 tabbladen
    excel_path = "/tmp/vergelijking_resultaat.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Werkprocessen")
        samenvatting.to_excel(writer, index=False, sheet_name="Samenvatting")

    return df
