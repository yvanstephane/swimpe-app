# -*- coding: utf-8 -*-
"""volontariat_flux.py — flux « origine -> programme » du type Volontariat.

programmes(code_orig) : programmes de volontariat (categorie=="volontariat"
    dans plans_pays_v1.json) actifs (plan_actif:CODE) et eligibles pour le
    pays d'origine (eligibilite: TOUS | AFRIQUE via meta.afrique_iso | liste).
rendre(code, code_orig, ORIGINES, LG) : plan client (sans notes internes)
    + offres liees (weltwärts→DE, France→FR).
"""
import streamlit as st

MAP_OFFRES = {"DE-WW": "DE", "FR-VOL": "FR"}


def _kb():
    import moteur_plans
    return moteur_plans._kb()


def _actif(code):
    try:
        import offres_sync
        return offres_sync.param(f"plan_actif:{code}", "1") != "0"
    except Exception:
        return True


def _afrique(kb):
    for v in ([kb] + [x for x in kb.values() if isinstance(x, dict)]):
        if "afrique_iso" in v:
            return {str(c).upper() for c in v["afrique_iso"]}
    return set()


def _eligible(entree, kb, code_orig):
    if not code_orig:
        return True
    e = entree.get("eligibilite", "TOUS")
    co = str(code_orig).upper()
    if isinstance(e, dict):  # patch_elig_fin : exclusion « tous sauf »
        sauf = {str(c).upper() for c in e.get("sauf", [])}
        return co not in sauf
    if isinstance(e, str):
        e = e.strip().upper()
        if e in ("", "TOUS"):
            return True
        if e == "AFRIQUE":
            return co in _afrique(kb)
        return co == e
    return co in {str(c).upper() for c in e}


def programmes(code_orig=None):
    """[(code, libelle_ecran)] des programmes visibles pour cette origine."""
    kb = _kb()
    out = []
    for c, d in kb.get("destinations", {}).items():
        if d.get("categorie") != "volontariat":
            continue
        if not _actif(c):
            continue
        if not _eligible(d, kb, code_orig):
            continue
        out.append((c, d.get("libelle_ecran", c)))
    return out


def rendre(code, code_orig, ORIGINES, LG="fr"):
    import moteur_plans
    if LG != "fr":
        st.caption("🌐 " + {"en": "Programme content in French.",
                            "es": "Contenido del programa en francés.",
                            "pt": "Conteúdo do programa em francês.",
                            "zh": "项目内容为法语。",
                            "ar": "محتوى البرنامج بالفرنسية.",
                            "ja": "プログラム内容はフランス語です。",
                            "ko": "프로그램 내용은 프랑스어입니다.",
                            "id": "Konten program dalam bahasa Prancis."
                            }.get(LG, "Contenu du programme en français."))
    try:
        res = moteur_plans.generer_plan(code, code_orig, ORIGINES)
    except TypeError:
        res = moteur_plans.generer_plan(code, code_orig, ORIGINES, "")
    plan = res[0] if isinstance(res, tuple) else res
    st.markdown(plan)   # notes internes volontairement NON affichees

    dest = MAP_OFFRES.get(code)
    if not dest:
        return
    try:
        try:
            from opportunites_ui import DB
        except Exception:
            DB = str(Path := __import__("pathlib").Path(__file__)
                     .resolve().parents[2] / "data" / "mobilite.db")
        import sqlite3
        con = sqlite3.connect(str(DB))
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM opportunites WHERE destination=? AND "
            "type='volontariat' AND IFNULL(statut,'') != 'doublon' "
            "ORDER BY id", (dest,)).fetchall()
        con.close()
    except Exception:
        rows = []
    ok = []
    for r in rows:
        elig = (r["origines_eligibles"] or "TOUS").strip().upper()
        if elig == "TOUS" or str(code_orig).upper() in                 [c.strip() for c in elig.split(",")]:
            ok.append(dict(r))
    if not ok:
        return
    st.markdown("#### 📌 " + {"fr": "Offres liées à ce programme"}.get("fr"))
    for o in ok:
        with st.expander(f"🤝 {o.get('titre', '')}"):
            if o.get("montant"):
                st.write(o["montant"])
            if o.get("source_url"):
                st.link_button("🔗 Voir l'offre", o["source_url"])
