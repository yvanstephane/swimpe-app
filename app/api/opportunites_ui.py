# =============================================================================
# opportunites_ui.py — v2 — Contenu par TYPE DE PROJET (page résultat)
# Stage/Emploi : offres de la base + JOB BOARD en direct (jobs_api/Adzuna).
# Liens externes JAMAIS montrés au visiteur pour emploi/stage (référence à
# indiquer dans le formulaire) ; l'admin voit les liens. Bourses : liens OK.
# =============================================================================
import streamlit as st
import sqlite3

DB = "data/mobilite.db"

try:
    import jobs_api
except Exception:
    jobs_api = None
try:
    import espace
except Exception:
    espace = None

TYPES_PAR_PROJET = {
    "Stage / Emploi étudiant": ("emploi", "stage"),
    "Métier spécialisé": ("metier",),
    "Sport": ("sport",),
    "Art": ("art",),
    "Volontariat": ("volontariat",),
}
ICONES = {"emploi": "💼", "stage": "🧑‍💻", "bourse": "💰", "formation": "🎓", "metier": "🔧", "sport": "🏆", "art": "🎨", "volontariat": "🤝"}


def _est_admin():
    try:
        return bool(espace and espace.est_admin())
    except Exception:
        return False


def _offres(dest_code, types, code_orig):
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        q = ",".join("?" * len(types))
        rows = con.execute(
            f"SELECT * FROM opportunites WHERE destination=? AND type IN ({q}) AND IFNULL(statut,'') != 'doublon' "
            "ORDER BY type, id", (dest_code, *types)).fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        con.close()
    ok = []
    for r in rows:
        elig = (r["origines_eligibles"] or "TOUS").strip().upper()
        if elig == "TOUS" or code_orig.upper() in [c.strip() for c in elig.split(",")]:
            ok.append(dict(r))
    return ok


def afficher(type_c, dest_code, code_orig, tr, poste="", domaine=""):
    """Affiche le contenu spécifique au projet. Retourne True si le mode
    « opportunités » est actif (→ ui.py masque les procédures d'études)."""
    types = TYPES_PAR_PROJET.get(type_c)
    if not types:
        return False           # Formation (admission) : comportement normal

    try:
        import offres_sync
        offres_sync.sync_si_necessaire(dest_code)   # rafraîchissement continu
        _liens = offres_sync.liens_actifs()
        _desc = offres_sync.descriptions_actives()
    except Exception:
        _liens = False
        _desc = True
    admin = _est_admin()
    est_bourse = (type_c == "Bourse")
    titres = {"Volontariat": "🤝 Programmes de volontariat vérifiés",
              "Stage / Emploi étudiant": "💼 Offres de stage & d'emploi étudiant",
              "Métier spécialisé": "🔧 Métiers spécialisés qui recrutent à l'international",
              "Bourse": "💰 Bourses ouvertes à ton profil", "Sport": "🏆 Sport", "Art": "🎨 Art"}
    st.markdown("### " + tr(titres.get(type_c, "Offres")))
    if type_c in ("Sport", "Art", "Volontariat"):
        _msg_sa = {"Volontariat": "🤝 Renseigne ton domaine et ta destination ci-dessus. Des programmes officiels vérifiés (weltwärts, Service Civique, VSI…) seront listés ici. ⚠️ Les candidatures aux programmes officiels de volontariat sont GRATUITES : aucun organisme sérieux ne facture un placement — méfie-toi de toute demande de paiement.",
                   "Sport": "🏆 Renseigne ta discipline et ta destination ci-dessus. Des programmes vérifiés (académies, bourses sportives universitaires, clubs) seront listés ici. ⚠ Un vrai club, une université ou un agent sérieux ne demande jamais d'argent pour une simple candidature : méfie-toi de toute demande de paiement en amont.",
                   "Art": "🎨 Renseigne ta discipline et ta destination ci-dessus. Des programmes vérifiés (écoles d'art, résidences, appels à candidature, visa artiste) seront listés ici. ⚠ Une école ou une résidence sérieuse ne fait pas payer une candidature : méfie-toi des intermédiaires qui réclament des frais en amont."}
        st.info(tr(_msg_sa[type_c]))

    # ---- Règles d'admissibilité (table eligibilite, gérée en admin) ----
    _types_ouverts = tuple(types)
    try:
        import eligibilite as _elig
        _lab = {"emploi": "emploi", "stage": "stage", "metier": "métier"}
        _notes_vues = []
        _ouverts, _bloques = [], []
        for _t in types:
            _ok_e, _note_e = _elig.autorise(dest_code, _t, code_orig)
            if _note_e and _note_e not in _notes_vues:
                _notes_vues.append(_note_e)
                st.info("🛂 " + tr(_note_e))
            (_ouverts if _ok_e else _bloques).append(_t)
        _types_ouverts = tuple(_ouverts)
        if _bloques and not _ouverts:
            st.warning("⛔ " + tr("D'après nos règles d'admissibilité, cette "
                       "voie n'est pas ouverte depuis ton pays d'origine. "
                       "Décris ton projet dans le formulaire en bas de page : "
                       "on te proposera une alternative réaliste."))
        elif _bloques:
            _o = ", ".join(_lab.get(t, t) for t in _ouverts)
            _b = ", ".join(_lab.get(t, t) for t in _bloques)
            st.warning(tr(f"⚠️ Depuis ton pays : ✅ {_o} ouvert · ⛔ {_b} bloqué. "
                          "On n'affiche que les offres ouvertes ; pour le reste, "
                          "décris ton projet dans le formulaire en bas de page."))
    except Exception:
        _types_ouverts = tuple(types)

    offres = _offres(dest_code, _types_ouverts, code_orig) if _types_ouverts else []
    if poste:
        try:
            import recherche_poste
            offres = recherche_poste.filtre(offres, poste)
        except Exception:
            pass
    for o in offres:
        ic = ICONES.get(o.get("type", ""), "📌")
        with st.expander(f"{ic} {tr(o['titre'])}"):
            if admin or _desc:
                if o.get("montant"):
                    st.markdown("**" + tr("Montant / rémunération :") + "** " + tr(o["montant"]))
                if o.get("niveau"):
                    st.markdown("**" + tr("Niveau :") + "** " + tr(o["niveau"]))
                if o.get("domaine"):
                    st.markdown("**" + tr("Domaine :") + "** " + tr(o["domaine"]))
                if o.get("deadline"):
                    st.markdown("**" + tr("Date limite :") + "** " + o["deadline"])
            else:
                st.caption("🔒 " + tr("Description réservée — contacte-nous via le "
                                      "formulaire en bas de page."))
            if o.get("source_url"):
                if admin or _liens or o.get("type") in ("sport", "art", "volontariat"):
                    lib = "🔗 " + (tr("Lien (admin)") if admin and not _liens
                                   else tr("Voir l'offre"))
                    st.link_button(lib, o["source_url"])
                else:
                    st.caption("📌 " + tr("Référence à indiquer dans le formulaire :")
                               + f" OPP-{o.get('id', '')}")

    # ---- Job board en direct (API), pour Stage / Emploi uniquement ----
    n_live = 0
    if not est_bourse and jobs_api is not None:
        if jobs_api.disponible() and jobs_api.couvre(dest_code):
            _tl = tuple(t for t in (("metier",) if type_c == "Métier spécialisé"
                                    else ("stage", "emploi")) if t in _types_ouverts)
            if _tl:
                n_live = jobs_api.afficher(dest_code, tr, admin=admin,
                                           code_orig=code_orig, types_live=_tl,
                                           poste=poste, domaine=domaine)
        elif admin and not jobs_api.disponible():
            st.caption("⚙️ Job board en direct inactif : ajoute ADZUNA_APP_ID et "
                       "ADZUNA_APP_KEY dans le fichier .env (compte gratuit sur "
                       "developer.adzuna.com).")

    if not offres and n_live == 0:
        st.info(tr("Aucune offre correspondant à ton pays d'origine n'est "
                   "référencée pour cette destination pour le moment. "
                   "Décris ton projet dans le formulaire en bas de page : "
                   "notre équipe fera une recherche ciblée pour toi."))
        return True

    st.caption(tr("Intéressé·e par une de ces offres ? Indique sa référence "
                  "dans le formulaire en bas de page, on s'occupe du dossier."))
    return True
