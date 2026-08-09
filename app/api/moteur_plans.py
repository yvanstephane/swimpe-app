# =============================================================================
# moteur_plans.py — Moteur de plans d'accompagnement (écran admin)
# Principe : AUCUN fait inventé. Tout vient de data/plans_pays_v1.json
# (base vérifiée le 2026-07-13, sources dans le JSON).
# v1.2 : rendu GÉNÉRIQUE piloté par le JSON — pour ajouter une destination
# (CA, DE, …), ÉDITER data/plans_pays_v1.json, jamais ce fichier.
# Le LLM local (optionnel) ne fait que reformuler — prompt verrouillé.
# Accès : ?page=plans (admin uniquement, gating fait par ui.py).
# =============================================================================
import json
import os
from datetime import date
from pathlib import Path

import streamlit as st

# ── Base de connaissances ────────────────────────────────────────────────────

def _kb_path():
    p = Path("data/plans_pays_v1.json")
    if p.exists():
        return p
    return Path(__file__).resolve().parents[2] / "data" / "plans_pays_v1.json"

@st.cache_data(show_spinner=False)
def _kb():
    with open(_kb_path(), encoding="utf-8") as f:
        return json.load(f)

def couvertes():
    """Codes destination couverts par la base de faits (console & co)."""
    return set(_kb()["destinations"].keys())

# ── Dates dynamiques (déterministes) ────────────────────────────────────────

def _prochaine(jour, mois):
    """Prochaine occurrence annuelle d'une date (ex. click day)."""
    auj = date.today()
    annee = auj.year if (auj.month, auj.day) <= (mois, jour) else auj.year + 1
    return date(annee, mois, jour)

def _fmt(d):
    MOIS = ["", "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return f"{d.day} {MOIS[d.month]} {d.year}"

def _dates_ctx():
    """Toutes les dates récurrentes, calculées depuis aujourd'hui."""
    return {
        "cd_agricole":  _fmt(_prochaine(12, 1)),
        "cd_tourisme":  _fmt(_prochaine(9, 2)),
        "cd_groupe1":   _fmt(_prochaine(16, 2)),
        "cd_groupe2":   _fmt(_prochaine(18, 2)),
        "ares_ouverture": _fmt(_prochaine(4, 8)),
        "ares_cloture":   _fmt(_prochaine(19, 9)),
        "annee":        str(date.today().year),
        "annee_p1":     str(date.today().year + 1),
    }

# ── Génération du plan (100 % déterministe) ─────────────────────────────────

def _nom_pays(code, ORIGINES):
    for nom, (c, _) in ORIGINES.items():
        if c == code:
            return nom
    return code

def _rendre_etape(i, et, dts):
    txt = (f"**Étape {i} — {et['titre']}**  \n"
           f"{et['detail'].format(**dts)}"
           + (f"  \n🔗 {et['lien']}" if et.get("lien") else ""))
    for r in et.get("ressources", []):
        txt += (f"\n  - 📚 {r['nom']}" + (f" → {r['url']}" if r.get("url") else ""))
    return txt

def generer_plan(dest, code_orig, ORIGINES, offre_txt=""):
    """Retourne (plan_client_md, notes_admin_md). Zéro invention."""
    kb = _kb()
    dts = _dates_ctx()
    pays = _nom_pays(code_orig, ORIGINES)
    afrique = code_orig in kb["meta"]["afrique_iso"]

    lignes, notes = [], []
    ref = f" — offre : {offre_txt[:80].strip()}" if offre_txt.strip() else ""

    if dest == "IT":
        it = kb["destinations"]["IT"]
        g1 = code_orig in it["groupe1"]["pays"]
        groupe = it["groupe1"] if g1 else it["groupe2"]
        lignes.append(f"# 🇮🇹 Plan d'accompagnement — {pays} → Italie{ref}\n")
        lignes.append(f"**Ta situation** : {groupe['libelle_client'].format(**dts)}\n")
        for i, et in enumerate(it["etapes_communes"], 1):
            lignes.append(_rendre_etape(i, et, dts))
        # Canaux stratégiques pour le groupe 2 (faits vérifiés)
        if not g1:
            lignes.append("\n## 💡 Deux portes moins connues (ouvertes à ta nationalité)\n")
            for canal in it["canaux_groupe2"]:
                lignes.append(f"**{canal['titre']}**  \n{canal['detail'].format(**dts)}")
        # Badanti : toujours (aucune restriction)
        lignes.append(f"\n**{it['badanti']['titre']}**  \n"
                      + it["badanti"]["detail"].format(**dts))
        if it.get("bouclier"):
            lignes.append("\n" + it["bouclier"])
        if code_orig in it["alertes_pays"]:
            lignes.append(f"\n⚠️ **Spécifique {pays}** : "
                          + it["alertes_pays"][code_orig])
        notes.extend(it["notes_admin"])

    elif dest == "BE":
        be = kb["destinations"]["BE"]
        if code_orig in be["pays_eligibles"]:
            lignes.append(f"# 🇧🇪 Plan d'accompagnement — {pays} → Belgique (bourse ARES){ref}\n")
            lignes.append(be["resume_client"].format(**dts) + "\n")
            for i, et in enumerate(be["etapes"], 1):
                lignes.append(_rendre_etape(i, et, dts))
            lignes.append("\n" + be["anti_arnaque"])
        else:
            lignes.append(f"# 🇧🇪 {pays} → Belgique — ARES non disponible\n")
            lignes.append(be["message_non_eligible"])
            if afrique:
                lignes.append("\n👉 **Alternative recommandée : la bourse "
                              "MasterCard Foundation** (ouverte à toute l'Afrique) — "
                              "voir le plan MCF.")
        notes.extend(be["notes_admin"])

    elif dest == "MCF":
        m = kb["destinations"]["MCF"]
        lignes.append(f"# 🎓 Plan d'accompagnement — {pays} → MasterCard Foundation{ref}\n")
        if not afrique:
            lignes.append("⚠️ Ce programme est réservé aux citoyens africains.")
        else:
            lignes.append(m["resume_client"] + "\n")
            for i, et in enumerate(m["etapes"], 1):
                lignes.append(_rendre_etape(i, et, dts))
            lignes.append("\n" + m["anti_arnaque"])
        notes.extend(m["notes_admin"])

    elif dest in kb["destinations"]:
        # ── Rendu GÉNÉRIQUE (v1.2) : toute destination décrite dans le JSON ──
        d = kb["destinations"][dest]
        lignes.append(f"# {d.get('drapeau', '🌍')} Plan d'accompagnement — "
                      f"{pays} → {d['nom']}{ref}\n")
        if d.get("resume_client"):
            lignes.append(d["resume_client"].format(**dts) + "\n")
        for i, et in enumerate(d.get("etapes", []), 1):
            lignes.append(_rendre_etape(i, et, dts))
        canaux = d.get("canaux", [])
        if canaux:
            lignes.append("\n## 💡 Les autres portes d'entrée (vérifiées)\n")
            for canal in canaux:
                lignes.append(f"**{canal['titre']}**  \n"
                              + canal["detail"].format(**dts))
        if d.get("bouclier"):
            lignes.append("\n" + d["bouclier"])
        if d.get("anti_arnaque"):
            lignes.append("\n" + d["anti_arnaque"])
        if code_orig in d.get("alertes_pays", {}):
            lignes.append(f"\n⚠️ **Spécifique {pays}** : "
                          + d["alertes_pays"][code_orig])
        notes.extend(d.get("notes_admin", []))

    else:
        dispo = ", ".join(sorted(kb["destinations"].keys()))
        lignes.append(f"Destination `{dest}` non couverte par la base "
                      f"(couvertes : {dispo}). Pour l'ajouter : éditer "
                      "data/plans_pays_v1.json — pas le code.")

    plan = "\n\n".join(lignes)
    plan += ("\n\n---\n*Plan généré le " + _fmt(date.today())
             + " à partir de sources officielles vérifiées (voir fiche pays). "
               "Les services Yorbity mentionnés sont optionnels — les candidatures "
               "aux programmes officiels sont GRATUITES.*")
    notes_md = ("### 📋 Notes internes (NE PAS copier au client)\n- "
                + "\n- ".join(notes)) if notes else ""
    return plan, notes_md

# ── Reformulation LLM optionnelle (verrouillée, dégradation propre) ─────────

def _personnaliser_ollama(plan_md, offre_txt, pays):
    import requests  # dispo dans le venv streamlit
    modele = os.environ.get("PLANS_MODEL", "llama3.3:70b")
    prompt = (
        "Reformule le plan ci-dessous pour t'adresser chaleureusement à un "
        f"client de {pays}" + (f" intéressé par cette offre : {offre_txt[:200]}"
        if offre_txt.strip() else "") + ".\n"
        "RÈGLES ABSOLUES : n'ajoute, ne modifie et ne supprime AUCUN fait, "
        "date, montant, liste de pays, condition ou lien. Ne donne aucun "
        "conseil juridique nouveau. Conserve tous les titres et la structure. "
        "Réponds uniquement avec le plan reformulé, en français.\n\n" + plan_md
    )
    r = requests.post("http://localhost:11434/api/generate",
                      json={"model": modele, "prompt": prompt, "stream": False},
                      timeout=180)
    r.raise_for_status()
    return r.json().get("response", "").strip() or plan_md

# ── Écran admin ──────────────────────────────────────────────────────────────

# --- Tri des noms sans accents (Sénégal, Bénin retrouvent leur place) ---
_ACCENTS = str.maketrans(
    "àáâãäåçèéêëìíîïñòóôõöùúûüýÿ",
    "aaaaaaceeeeiiiinooooouuuuyy")
def _tri_sans_accents(_s):
    return _s.lower().translate(_ACCENTS)


def ecran(ORIGINES=None):
    """Écran ?page=plans. True si affiché (l'appelant gère est_admin)."""
    try:
        page = st.query_params.get("page")
    except Exception:  # anciennes versions Streamlit
        page = (st.experimental_get_query_params().get("page") or [None])[0]
    if page != "plans":
        return False

    if ORIGINES is None:
        from pays_monde import ORIGINES_MONDE as ORIGINES

    st.title("🧭 Moteur de plans d'accompagnement")
    st.caption("Faits 100 % issus de la base vérifiée `data/plans_pays_v1.json` "
               f"(màj {_kb()['meta']['maj']}). Le moteur n'invente rien.")

    kb = _kb()
    codes = list(kb["destinations"].keys())
    libelles = {c: kb["destinations"][c].get("libelle_ecran", c) for c in codes}

    # --- patch_plans_actifs : activer/desactiver chaque programme (admin) ----
    # Reglage dans config_params, cle plan_actif:<CODE> (via offres_sync,
    # meme convention que source_active:<nom> du registre). Defaut = actif.
    def _plan_actif(_c):
        try:
            import offres_sync
            return offres_sync.param(f"plan_actif:{_c}", "1") != "0"
        except Exception:
            return True

    with st.expander("⚙️ Programmes visibles"):
        st.caption("Décoché = retiré du menu déroulant ci-dessous. "
                   "Réglage global (config_params · plan_actif:CODE). "
                   "Tout décocher = tout afficher (repli).")
        try:
            import offres_sync as _osync
        except Exception:
            _osync = None
            st.warning("offres_sync indisponible : réglage en lecture seule.")
        for _c in codes:
            _on = _plan_actif(_c)
            _nv = st.checkbox(libelles.get(_c, _c), value=_on,
                              key=f"plan_act_{_c}")
            if _osync is not None and _nv != _on:
                try:
                    _osync.definir_param(f"plan_actif:{_c}", "1" if _nv else "0")
                except Exception as _e:
                    st.error(f"Enregistrement impossible : {_e}")
                else:
                    st.rerun()

    codes_visibles = [c for c in codes if _plan_actif(c)] or codes
    # --- fin patch_plans_actifs ---------------------------------------------

    col1, col2 = st.columns(2)
    with col1:
        noms = sorted(ORIGINES.keys(), key=_tri_sans_accents)
        pays_nom = st.selectbox("🛂 Nationalité du client (passeport)", noms)
        code_orig = ORIGINES[pays_nom][0]
    with col2:
        dest = st.selectbox("🎯 Programme / destination", codes_visibles,
                            format_func=libelles.get)

    offre = st.text_area("📋 Offre d'emploi ou référence (optionnel)",
                         placeholder="Colle ici le titre/texte de l'offre ou sa référence…",
                         height=100)
    ia = st.checkbox("🤖 Reformuler pour ce client (Ollama local — "
                     "n'ajoute aucun fait)", value=False)

    if st.button("⚙️ Générer le plan", type="primary"):
        plan, notes = generer_plan(dest, code_orig, ORIGINES, offre)
        if ia:
            with st.spinner("Reformulation locale en cours…"):
                try:
                    plan = _personnaliser_ollama(plan, offre, pays_nom)
                except Exception as e:
                    st.warning(f"Ollama indisponible ({e}) — plan standard affiché.")
        st.subheader("Plan client (copier-coller)")
        st.code(plan, language="markdown")
        with st.expander("👁️ Aperçu mis en forme"):
            st.markdown(plan)
        if notes:
            st.divider()
            st.markdown(notes)
    return True

# _maj_ressources_etapes_v1
# _lot23_plans_v1
