# =============================================================================
# console_accompagnement.py — Console d'accompagnement admin (v2a)
# Accès : ?page=console (gating admin fait par ui.py).
# Principes : profil ISOLÉ (session acc_*), diagnostic sourcé
# (data/refus_par_pays_v1.json), offres via jobs_api (sources réelles,
# AUCUNE modification), plan via moteur_plans (base vérifiée, sans IA).
# =============================================================================
import json
import re
from datetime import date
from pathlib import Path

import streamlit as st

import jobs_api
import moteur_plans

_REF_RE = re.compile(r"^(?:[A-Z]{2,4}-\d+|OPP-\d+)$")

# ── Données refus ────────────────────────────────────────────────────────────

def _refus_path():
    p = Path("data/refus_par_pays_v1.json")
    if p.exists():
        return p
    return Path(__file__).resolve().parents[2] / "data" / "refus_par_pays_v1.json"

@st.cache_data(show_spinner=False)
def _refus():
    with open(_refus_path(), encoding="utf-8") as f:
        return json.load(f)

# ── Zone 0 : profil client (état isolé acc_*) ───────────────────────────────

def _zone_profil(D, ORIGINES):
    st.markdown("#### 👤 Profil du client")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        type_c = st.selectbox("📌 Type de projet",
                              ["Métier spécialisé", "Stage / Emploi",
                               "Bourse / Études"],
                              key="acc_type")
    with c2:
        noms = sorted(ORIGINES.keys())
        defaut = noms.index("Cameroun") if "Cameroun" in noms else 0
        pays_nom = st.selectbox("🌍 Pays d'origine", noms, index=defaut,
                                key="acc_orig")
        code_orig = ORIGINES[pays_nom][0]
    with c3:
        codes = sorted(D.keys(), key=lambda c: D[c]["nom"])
        defaut_d = codes.index("IT") if "IT" in codes else 0
        dest = st.selectbox("🎯 Destination", codes, index=defaut_d,
                            key="acc_dest",
                            format_func=lambda c: f"{D[c].get('flag','')} {D[c]['nom']}")
    with c4:
        domaine = st.text_input("📚 Domaine (optionnel)", key="acc_dom")
    return type_c, pays_nom, code_orig, dest, domaine

# ── Zone 1 : recherche ──────────────────────────────────────────────────────

def _zone_recherche():
    q = st.text_input("🔍 Métier ou mots-clés de l'offre",
                      key="acc_q",
                      placeholder="électricien, plombier, soudeur…")
    q = (q or "").strip()
    if q and _REF_RE.match(q.upper()):
        st.caption("ℹ️ Recherche par référence exacte : arrive en v2b — "
                   "recherche par mots-clés lancée en attendant.")
    return q

# ── Zone 2 : diagnostic refus ───────────────────────────────────────────────

def _zone_diagnostic(code_orig, pays_nom, dest, D=None):  # _lot5_diagnostic_v1
    R = _refus()
    nom_dest = (D or {}).get(dest, {}).get("nom", dest)
    st.markdown(f"#### 🚦 Diagnostic — {pays_nom} → {nom_dest}")

    # Un SEUL chiffre : celui de la destination choisie (règle générale).
    par_dest = R.get("taux_par_destination", {})
    schengen = set(R.get("pays_schengen", []))
    regime = None  # (libelle, valeur_affichee, source)

    if dest in par_dest:                       # destination à chiffre propre (ex. CA)
        d = par_dest[dest]
        src = R["sources"].get(d.get("source_key", ""), "")
        regime = (d["libelle"], f"~{d['taux']:.0f} %{d.get('suffixe', '')}", src)
    elif dest in schengen:                     # destination espace Schengen
        taux_pays = R["taux_schengen_pays"].get(code_orig)
        src = R["sources"]["schengen"]
        if taux_pays is not None:
            regime = ("Refus visas Schengen — " + pays_nom,
                      f"~{taux_pays:.0f} %", src)
        else:
            regime = ("Refus Schengen (moy. demandeurs africains)",
                      f"~{R['taux_schengen_zone_afrique']:.0f} %", src)

    if regime is None:                         # pas de statistique fiable : honnêteté
        st.caption(f"ℹ️ Pas de statistique de refus consolidée pour {nom_dest} "
                   "dans notre base — le plan d'accompagnement ci-dessous reste "
                   "valable.")
        return

    libelle, valeur, src = regime
    st.metric(libelle, valeur, help=src)
    st.markdown("**Les causes principales — et comment on les répare :**")
    for c in R["causes_principales"]:
        st.markdown(f"- 🔴 **{c['cause']}** ({c['part']} % des refus) "
                    f"→ 🟢 service **{c['service']}** : {c['remede']}")
    spec = R["specificites"].get(dest)
    if spec:
        st.markdown(f"- ⚠️ **Spécifique {nom_dest}** : {spec}")
    st.caption("Trois causes sur quatre se réparent dans le dossier. "
               "Sources : " + R["sources"]["note"])

# ── Zone 3 : offres réelles (jobs_api, non modifié) ─────────────────────────

def _zone_offres(type_c, dest, code_orig, poste, domaine):
    st.markdown("#### 📋 Offres (sources officielles, à jour)")
    if not jobs_api.disponible():
        st.caption("⚙️ Job board inactif : clés ADZUNA manquantes dans .env.")
        return
    if not jobs_api.couvre(dest):
        st.info("Pas de source d'offres en direct pour cette destination — "
                "le plan d'accompagnement reste disponible ci-dessous.")
        return
    types_live = ("metier",) if type_c == "Métier spécialisé" else ("stage", "emploi")
    jobs_api.afficher(dest, _tr, admin=True, code_orig=code_orig,
                      types_live=types_live, poste=poste, domaine=domaine)

def _tr(s):
    return s  # console admin : français

# ── Zone 4 : plan daté (moteur vérifié, sans IA) ────────────────────────────

def _chip_compte_a_rebours(libelle, d):
    j = (d - date.today()).days
    st.markdown(f"`{libelle} : {moteur_plans._fmt(d)} · J−{j}`")

def _zone_plan(type_c, code_orig, pays_nom, dest, ORIGINES, q):
    st.markdown("#### 🧭 Plan d'accompagnement")
    bourse = type_c == "Bourse / Études"
    if bourse:
        progs = []
        if dest == "BE":
            progs.append(("BE", "🇧🇪 Bourse ARES (Belgique)"))
        elif dest in ("CA", "DE") and dest in moteur_plans.couvertes():
            _lib = moteur_plans._kb()["destinations"][dest].get(
                "libelle_ecran", dest)
            progs.append((dest, _lib + " — volet études"))
        progs.append(("MCF", "🎓 MasterCard Foundation (multi-destinations)"))
        if dest == "IT":
            st.caption("💡 Italie + études : la passerelle « permis études → "
                       "travail hors quota » est dans la fiche Italie.")
        prog = st.radio("Programme", [p[0] for p in progs],
                        format_func=dict(progs).get, horizontal=True,
                        key="acc_prog")
        cible = prog
    else:
        cible = dest
        if dest == "IT":
            c1, c2, c3 = st.columns(3)
            with c1:
                _chip_compte_a_rebours("Précompilation ALI (ouverture)",
                                       moteur_plans._prochaine(23, 10))
            with c2:
                _chip_compte_a_rebours("Click day quota réservé",
                                       moteur_plans._prochaine(16, 2))
            with c3:
                _chip_compte_a_rebours("Click day quote générale",
                                       moteur_plans._prochaine(18, 2))
    offre_txt = st.text_input("Offre ou référence pour personnaliser le plan "
                              "(copier le titre depuis la liste ci-dessus)",
                              value=q, key="acc_offre")
    if st.button("⚙️ Générer le plan", type="primary", key="acc_go"):
        if cible not in moteur_plans.couvertes():  # _lot4_console_v1
            st.info("Destinations couvertes par le moteur : "
                    + ", ".join(sorted(moteur_plans.couvertes()))
                    + ". Les autres s'ajoutent dans "
                      "data/plans_pays_v1.json.")
            return
        plan, notes = moteur_plans.generer_plan(cible, code_orig,
                                                ORIGINES, offre_txt)
        st.subheader("Plan client (copier-coller)")
        st.code(plan, language="markdown")
        with st.expander("👁️ Aperçu mis en forme"):
            st.markdown(plan)
        if notes:
            st.divider()
            st.markdown(notes)

# ── Écran ────────────────────────────────────────────────────────────────────

def ecran(D, ORIGINES):
    """Console ?page=console. True si affichée (admin géré en amont)."""
    try:
        page = st.query_params.get("page")
    except Exception:
        page = (st.experimental_get_query_params().get("page") or [None])[0]
    if page != "console":
        return False

    st.title("🧭 Console d'accompagnement")
    st.caption("Profil isolé · diagnostic sourcé · offres officielles en "
               "direct · plan 100 % déterministe (base vérifiée "
               f"{moteur_plans._kb()['meta']['maj']}).")

    type_c, pays_nom, code_orig, dest, domaine = _zone_profil(D, ORIGINES)
    st.divider()
    q = _zone_recherche()
    st.divider()
    _zone_diagnostic(code_orig, pays_nom, dest, D)
    st.divider()
    if type_c != "Bourse / Études":
        _zone_offres(type_c, dest, code_orig, q, domaine)
        st.divider()
    _zone_plan(type_c, code_orig, pays_nom, dest, ORIGINES, q)
    return True
