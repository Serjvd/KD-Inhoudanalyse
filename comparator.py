import pdfplumber
import re
import pandas as pd
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

def extract_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text

def extract_kerntaken(text):
    pattern = r'(B\d+-K\d+):\s*(.*?)\n((?:.(?!B\d+-K\d+:))*.)'
    matches = re.findall(pattern, text, re.DOTALL)

    kerntaken = []
    for code, titel, inhoud in matches:
        kerntaken.append({
            "code": code.strip(),
            "titel": titel.strip(),
            "tekst": inhoud.strip()
        })
    return kerntaken

def vergelijk_kds(oud_path, nieuw_path):
    oud_text = extract_text(oud_path)
    nieuw_text = extract_text(nieuw_path)

    oud_kerntaken = extract_kerntaken(oud_text)
    nieuw_kerntaken = extract_kerntaken(nieuw_text)

    resultaten = []
    gebruikte_nieuwe = set()

    for oud in oud_kerntaken:
        beste_match = None
        hoogste_score = -1
        for i, nieuw in enumerate(nieuw_kerntaken):
            if i in gebruikte_nieuwe:
                continue
            score = float(util.cos_sim(
                model.encode(oud["tekst"], convert_to_tensor=True),
                model.encode(nieuw["tekst"], convert_to_tensor=True)
            ))
            if score > hoogste_score:
                hoogste_score = score
                beste_match = nieuw
                beste_index = i

        if beste_match and hoogste_score > 0.6:
            gebruikte_nieuwe.add(beste_index)
            resultaten.append({
                "Oude code": oud["code"],
                "Nieuwe code": beste_match["code"],
                "Titel": oud["titel"],
                "Overeenkomst": f"{hoogste_score:.2f}",
                "Status": "Gewijzigd" if hoogste_score < 0.95 else "Ongewijzigd"
            })
        else:
            resultaten.append({
                "Oude code": oud["code"],
                "Nieuwe code": "",
                "Titel": oud["titel"],
                "Overeenkomst": "0.00",
                "Status": "Verwijderd"
            })

    for i, nieuw in enumerate(nieuw_kerntaken):
        if i not in gebruikte_nieuwe:
            resultaten.append({
                "Oude code": "",
                "Nieuwe code": nieuw["code"],
                "Titel": nieuw["titel"],
                "Overeenkomst": "0.00",
                "Status": "Toegevoegd"
            })

    return pd.DataFrame(resultaten)
