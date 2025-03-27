import pdfplumber
import re
from typing import Dict, List


def extracteer_data(pdf_path: str) -> Dict:
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    data = {
        "metadata": extracteer_metadata(text),
        "kerntaken": extracteer_kerntaken(text),
        "werkprocessen": extracteer_werkprocessen(text),
        "context": extracteer_sectie(text, "Context"),
        "beroepshouding": extracteer_sectie(text, "Typerende beroepshouding"),
        "resultaat": extracteer_sectie(text, "Resultaat van de beroepsgroep"),
        "vakkennis_vaardigheden": extracteer_opsomming(text, "Vakkennis en vaardigheden")
    }

    return data


def extracteer_metadata(text: str) -> Dict:
    crebo_dossier = re.search(r"Crebonummer kwalificatiedossier\s*:?\s*(\d+)", text)
    crebo_kwalificatie = re.search(r"Crebonummer kwalificatie\s*:?\s*(\d+)", text)
    naam = re.search(r"Naam kwalificatie\s*:?\s*(.+)", text)
    versie = re.search(r"Versie\s*:?\s*([\w\-/]+)", text)
    geldig = re.search(r"Geldig vanaf\s*:?\s*([\w\-/]+)", text)

    return {
        "crebonr_dossier": crebo_dossier.group(1) if crebo_dossier else "-",
        "crebonr_kwalificatie": crebo_kwalificatie.group(1) if crebo_kwalificatie else "-",
        "naam_kwalificatie": naam.group(1).strip() if naam else "-",
        "versie": versie.group(1) if versie else "-",
        "geldig_vanaf": geldig.group(1) if geldig else "-"
    }


def extracteer_kerntaken(text: str) -> List[Dict]:
    pattern = r"(B\d+-K\d+)\s+([^\n]+)"
    matches = re.findall(pattern, text)
    kerntaken = []
    for code, naam in matches:
        kerntaken.append({"code": code.strip(), "naam": naam.strip()})
    return kerntaken


def extracteer_werkprocessen(text: str) -> List[Dict]:
    pattern = r"(B\d+-K\d+-W\d+)\s+([^\n]+)"
    matches = re.findall(pattern, text)
    werkprocessen = []
    for code, naam in matches:
        werkprocessen.append({"code": code.strip(), "naam": naam.strip()})
    return werkprocessen


def extracteer_sectie(text: str, titel: str) -> str:
    pattern = rf"{titel}\n+(.+?)(?:\n\n|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else "-"


def extracteer_opsomming(text: str, kop: str) -> List[str]:
    pattern = rf"{kop}\n+(.*?)\n\n"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return []
    inhoud = match.group(1)
    regels = [r.strip("•- ") for r in inhoud.split("\n") if r.strip()]
    return regels
