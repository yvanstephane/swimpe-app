# =============================================================================
# admin_projets.py — Dashboard admin par TYPE DE PROJET (multilingue)
# Format anti-erreur : une LISTE DÉROULANTE par rôle (⭐ dans le libellé des
# pays validés, ✅ si proposé au visiteur) + un interrupteur pour le pays
# choisi. On ne modifie qu'un pays à la fois : aucun effacement accidentel.
# =============================================================================
import streamlit as st
import config_projets as cp
from traduction import traduire
try:
    from pays_i18n import nom_pays
except Exception:
    def nom_pays(nom, lang):
        return nom


def _lang():
    return st.session_state.get("lang", "fr")


def _tr(txt):
    return traduire(txt, _lang())


def _seed_initial(D, ORIGINES):
    """Pose les étoiles automatiques au premier lancement."""
    detaillees = [c for c in D if D[c].get("portail")]
    noms_det = [D[c]["nom"] for c in detaillees]
    cp.seed_etoiles("Formation (admission)", "destination", noms_det)
    avec_bourses = [D[c]["nom"] for c in detaillees
                    if D[c].get("bourses") and len(D[c]["bourses"]) > 0
                    and D[c]["bourses"][0][0]]
    cp.seed_etoiles("Bourse", "destination", avec_bourses)
    cp.seed_etoiles("Stage / Emploi étudiant", "destination", noms_det)
    toutes_orig = list(ORIGINES.keys())
    for proj in cp.PROJETS:
        cp.seed_etoiles(proj, "origine", toutes_orig)


def _panneau(projet, role, tous_noms, titre):
    """Liste déroulante + interrupteur : modification pays par pays, sans
    risque d'effacement accidentel."""
    st.markdown(f"### {titre}")
    lang = _lang()
    etat = cp.etat(projet, role)

    def _lbl(p):
        et, ac = etat.get(p, (0, 0))
        if et:
            prefixe = "⭐ "        # recherche validée
        elif ac:
            prefixe = "🔵 "        # FORCÉ : actif sans étoile
        else:
            prefixe = "◻️ "
        return prefixe + nom_pays(p, lang) + ("  ·  ✅" if ac else "")

    choix = st.selectbox(_tr("Choisir un pays"), tous_noms,
                         format_func=_lbl, key=f"sel_{role}_{projet}")
    et, ac = etat.get(choix, (0, 0))
    if et:
        st.caption("⭐ " + _tr("Recherche validée pour ce pays."))
    else:
        st.caption("◻️ " + _tr("Pas encore de fiche validée (activation = forçage)."))
    nouveau = st.toggle(_tr("Proposé au visiteur"),
                        value=bool(ac), key=f"tg_{role}_{projet}_{choix}")
    if nouveau != bool(ac):
        cp.definir(projet, role, choix, actif=nouveau)
        st.rerun()

    actifs = [p for p in tous_noms if etat.get(p, (0, 0))[1]]
    n_star = sum(1 for p in actifs if etat.get(p, (0, 0))[0])
    st.caption(f"**{len(actifs)}** {_tr('actifs')} · **{n_star}** ⭐ · "
               f"**{len(actifs) - n_star}** {_tr('forcés sans étoile')}")


def ecran(D, ORIGINES):
    """Éditeur admin par projet. True si affiché."""
    if not st.session_state.get("show_cfg_projets"):
        return False
    _seed_initial(D, ORIGINES)

    st.markdown("## 🎛 " + _tr("Configuration par projet"))
    st.caption(_tr("Choisis un type de projet, puis gère pays par pays. "
                   "⭐ = recherche validée (visible ici uniquement). "
                   "Un pays est proposé au visiteur s'il est activé."))

    projet = st.selectbox(_tr("Type de projet"), cp.PROJETS,
                          key="cfgp_projet", format_func=_tr)

    noms_dest = sorted({D[c]["nom"] for c in D})
    noms_orig = sorted(ORIGINES.keys())

    col1, col2 = st.columns(2)
    with col1:
        _panneau(projet, "destination", noms_dest, "🎯 " + _tr("Destinations"))
    with col2:
        _panneau(projet, "origine", noms_orig, "🌍 " + _tr("Origines"))

    st.divider()
    if st.button("← " + _tr("Retour"), key="cfgp_retour"):
        st.session_state.show_cfg_projets = False
        st.rerun()
    return True
