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

        # Verplaatsen logica: zelfde naam maar andere code
        verplaatst = False
        if oud.get("naam") == nieuw.get("naam") and oud != nieuw:
            verplaatst = True

        if verplaatst:
            impact = "Verplaatst"
            score = "Weinig impact"
            analyse = f"Werkproces is verplaatst van code {code} in oud dossier"
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
