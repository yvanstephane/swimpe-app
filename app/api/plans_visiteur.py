# -*- coding: utf-8 -*-
"""plans_visiteur.py — vue VISITEUR des plans d'accompagnement.

Ecran ?page=programmes (ou st.session_state.show_programmes).
Jumeau de moteur_plans.ecran, mais : accessible sans etre admin, SANS les
notes internes, et soumis a deux reglages admin (config_params) :
  plans_visiteur_actif   ("0" defaut) : vue activee ? (OFF par defaut)
  plans_visiteur_premium ("0" defaut) : reservee au Premium ?
Respecte aussi le panneau « ⚙️ Programmes visibles » (plan_actif:CODE).
"""
import streamlit as st

_ACCENTS = str.maketrans(
    "àáâãäåçèéêëìíîïñòóôõöùúûüýÿ",
    "aaaaaaceeeeiiiinooooouuuuyy")


def _tri(s):
    return s.lower().translate(_ACCENTS)


def _param(cle, defaut):
    try:
        import offres_sync
        return offres_sync.param(cle, defaut)
    except Exception:
        return defaut


def _tr(txt):
    try:
        from traduction import traduire
        return traduire(txt, st.session_state.get("lang", "fr"))
    except Exception:
        return txt


def _fermer():
    st.session_state.show_programmes = False
    try:
        if st.query_params.get("page") == "programmes":
            st.query_params.clear()
    except Exception:
        pass
    st.rerun()


def ecran(ORIGINES=None):
    """True si l'ecran a ete affiche (l'appelant fait st.stop())."""
    try:
        page = st.query_params.get("page")
    except Exception:
        page = None
    if page != "programmes" and not st.session_state.get("show_programmes"):
        return False

    # Interrupteur admin : vue coupee -> comme si la page n'existait pas.
    if _param("plans_visiteur_actif", "0") == "0":
        return False

    if ORIGINES is None:
        from pays_monde import ORIGINES_MONDE as ORIGINES

    import moteur_plans
    kb = moteur_plans._kb()
    codes = [c for c in kb["destinations"]
             if _param(f"plan_actif:{c}", "1") != "0"]         or list(kb["destinations"])
    libelles = {c: kb["destinations"][c].get("libelle_ecran", c) for c in codes}

    st.title("🗺️ " + _tr("Programmes d'accompagnement"))
    st.caption(_tr("Parcours officiels verifies, sources gouvernementales et "
                   "institutionnelles. Les candidatures aux programmes "
                   "officiels sont GRATUITES."))

    # ── Verrou Premium (optionnel, pilote par l'admin) ──
    if _param("plans_visiteur_premium", "0") == "1":
        est_prem = False
        try:
            import espace, auth
            u = espace.user_connecte()
            est_prem = bool(u) and auth.est_premium(u)
        except Exception:
            est_prem = False
        if not est_prem:
            st.info("💎 " + _tr("Cette section est reservee aux membres "
                                "Premium."))
            st.markdown(_tr("Programmes couverts :") + "  \n" +
                        "  \n".join(f"- {libelles[c]}" for c in codes))
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💎 " + _tr("Passer au Premium"),
                             type="primary", use_container_width=True,
                             key="pv_go_premium"):
                    st.session_state.show_programmes = False
                    st.session_state.show_premium = True
                    st.rerun()
            with c2:
                if st.button("← " + _tr("Retour"), use_container_width=True,
                             key="pv_retour_teaser"):
                    _fermer()
            return True

    # ── Vue complete ──
    col1, col2 = st.columns(2)
    with col1:
        noms = sorted(ORIGINES.keys(), key=_tri)
        pays_nom = st.selectbox("🛂 " + _tr("Ta nationalité (passeport)"), noms,
                                key="pv_origine")
        code_orig = ORIGINES[pays_nom][0]
    with col2:
        dest = st.selectbox("🎯 " + _tr("Programme / destination"), codes,
                            format_func=libelles.get, key="pv_dest")

    if st.button("🧭 " + _tr("Afficher le plan"), type="primary",
                 key="pv_generer"):
        try:
            res = moteur_plans.generer_plan(dest, code_orig, ORIGINES)
        except TypeError:
            res = moteur_plans.generer_plan(dest, code_orig, ORIGINES, "")
        plan = res[0] if isinstance(res, tuple) else res
        st.markdown(plan)   # notes internes volontairement NON affichees

    if st.button("← " + _tr("Retour"), key="pv_retour"):
        _fermer()
    return True
