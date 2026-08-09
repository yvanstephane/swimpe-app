# =============================================================================
# espace.py — Écrans de compte Yorbity (connexion, inscription, espace perso)
# S'appuie sur auth.py. Importé par ui.py.
# =============================================================================
import streamlit as st
import sqlite3, datetime
import auth
from i18n import t

DB = "data/mobilite.db"

def _lg():
    return st.session_state.get("lang", "fr")

# ----------------------------------------------------------------------------
# Helpers de session
# ----------------------------------------------------------------------------
def user_connecte():
    return st.session_state.get("user")

def est_admin():
    u = user_connecte()
    return u and u.get("role") == "admin"

def deconnexion():
    st.session_state.pop("user", None)

# ----------------------------------------------------------------------------
# Barre latérale : bloc compte (connexion / infos / déconnexion)
# ----------------------------------------------------------------------------
def bloc_compte_sidebar():
    auth.init_db()
    with st.sidebar:
        st.markdown("---")
        u = user_connecte()
        if u:
            st.markdown(f"👤 **{u['nom'] or u['email']}**")
            if auth.est_premium(u):
                st.success(t("premium_actif", _lg()))
            else:
                st.caption(t("compte_gratuit", _lg()))
            if st.button("🛠 Services & démarches", key="btn_boutique",
                         use_container_width=True):
                st.session_state.show_boutique = True
                st.rerun()
            if st.button(t("btn_deconnexion", _lg()), use_container_width=True):
                deconnexion()
                st.rerun()
        else:
            st.markdown("### " + t("compte_titre", _lg()))
            st.caption(t("compte_invite", _lg()))
            if st.button(t("btn_connexion", _lg()), use_container_width=True, type="primary"):
                st.session_state.show_auth = True
                st.rerun()

# ----------------------------------------------------------------------------
# Écran connexion / inscription (modale simulée en haut de page)
# ----------------------------------------------------------------------------
def ecran_auth(origines_dict):
    """Affiche l'écran de connexion/inscription. Retourne True si affiché (pour stopper le reste)."""
    if not st.session_state.get("show_auth"):
        return False

    st.markdown("## " + t("bienvenue", _lg()))
    onglet_co, onglet_in = st.tabs([t("onglet_connexion", _lg()), t("onglet_inscription", _lg())])

    with onglet_co:
        with st.form("form_connexion"):
            email = st.text_input(t("champ_email", _lg()))
            pwd = st.text_input(t("champ_pwd", _lg()), type="password")
            c1, c2 = st.columns(2)
            ok = c1.form_submit_button(t("btn_connecter", _lg()), type="primary", use_container_width=True)
            annul = c2.form_submit_button(t("btn_retour", _lg()), use_container_width=True)
            if ok:
                reussi, res = auth.connecter(email, pwd)
                if reussi:
                    st.session_state.user = res
                    st.session_state.show_auth = False
                    st.rerun()
                else:
                    st.error(res)
            if annul:
                st.session_state.show_auth = False
                st.rerun()
        if st.button("🔑 Mot de passe oublié ?", key="btn_mdp_oublie"):
            st.session_state.show_auth = False
            st.session_state.show_mdp_oublie = True
            st.session_state.mdpo_etape = 1
            st.rerun()

    with onglet_in:
        with st.form("form_inscription"):
            nom = st.text_input(t("champ_nom", _lg()))
            st.caption("🪪 " + t("nom_legal_note", _lg()))
            email = st.text_input(t("champ_email", _lg()) + " ")
            pays = st.selectbox(t("champ_pays", _lg()), ["—"] + sorted(origines_dict.keys()))
            tel = st.text_input(t("champ_tel", _lg()))
            st.caption("💬 " + t("tel_note", _lg()))  # patch_inscription_ux
            pwd = st.text_input(t("pwd_hint", _lg()), type="password")
            c1, c2 = st.columns(2)
            ok = c1.form_submit_button(t("btn_creer", _lg()), type="primary", use_container_width=True)
            annul = c2.form_submit_button(t("btn_retour", _lg()) + " ", use_container_width=True)
            if ok:
                if True:  # patch_inscription_ux : confirmation retiree (l'oeil natif du champ suffit)
                    reussi, res = auth.inscrire(email, nom, pwd,
                                                pays if pays != "—" else "", tel)
                    if reussi:
                        # connecter automatiquement après inscription
                        _, user = auth.connecter(email, pwd)
                        st.session_state.user = user
                        st.session_state.show_auth = False
                        st.success(t("compte_cree", _lg()))
                        st.rerun()
                    else:
                        st.error(res)
            if annul:
                st.session_state.show_auth = False
                st.rerun()

    st.info(t("donnees_protegees", _lg()))
    return True

# ----------------------------------------------------------------------------
# Sauvegarder un projet dans l'espace de l'utilisateur
# ----------------------------------------------------------------------------
def init_projets():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS projets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, date TEXT, origine TEXT, destination TEXT,
        type TEXT, niveau TEXT, domaine TEXT, statut TEXT DEFAULT 'nouveau')""")
    con.commit(); con.close()

def sauver_projet(user_id, origine, destination, type_, niveau, domaine):
    init_projets()
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO projets(user_id,date,origine,destination,type,niveau,domaine) "
                "VALUES(?,?,?,?,?,?,?)",
                (user_id, datetime.date.today().isoformat(),
                 origine, destination, type_, niveau, domaine))
    con.commit(); con.close()

def mes_projets(user_id):
    init_projets()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM projets WHERE user_id=? ORDER BY id DESC",
                       (user_id,)).fetchall()
    con.close()
    return rows


# ----------------------------------------------------------------------------
# Écran d'abonnement Premium
# ----------------------------------------------------------------------------
def ecran_premium():
    """Affiche les offres Premium et gère le paiement. Retourne True si affiché."""
    if not st.session_state.get("show_premium"):
        return False
    import paiement
    u = user_connecte()
    if not u:
        st.session_state.show_premium = False
        st.session_state.show_auth = True
        st.rerun()

    st.markdown("## ⭐ Passe au Premium")
    st.write("Le Premium débloque l'accompagnement personnalisé, les démarches "
             "déléguées et le suivi complet de tes dossiers.")

    if auth.est_premium(u):
        st.success(f"✅ Ton Premium est déjà actif jusqu'au {u['premium_jusqu']}.")

    if paiement.MODE != "reel":
        st.info(t("mode_test_info", _lg()))

    import offres_cfg, devises_cfg
    _offres = offres_cfg.toutes()
    cols = st.columns(max(1, len(_offres)))
    for col, (code, (label, prix, jours)) in zip(cols, _offres.items()):
        with col:
            st.markdown(f"### {label}")
            st.markdown(f"**{prix:g} €**")
            _aff = devises_cfg.prix_affiche(prix)
            if not _aff.endswith("€"):
                st.caption(f"≈ {_aff}")
            st.caption(f"{jours} " + t("jours", _lg()))
            if st.button(t("btn_choisir", _lg()), key=f"pay_{code}", use_container_width=True, type="primary"):
                try:
                    res = paiement.lancer_paiement(u, code)
                except Exception:
                    if getattr(paiement, "MODE", "test") != "reel":
                        res = {"ok": True, "mode": "test", "jours": jours}
                    else:
                        res = {"ok": False,
                               "message": "Offre non reliée au paiement réel — configuration requise."}
                if res["ok"]:
                    if res["mode"] == "test":
                        nouveau = auth.activer_premium(u["id"], res["jours"])
                        # rafraîchir la session avec la nouvelle date premium
                        st.session_state.user["premium_jusqu"] = nouveau
                        st.success(f"✅ Premium activé pour {res['jours']} jours (mode test) !")
                        st.balloons()
                    else:
                        st.markdown(f"### [👉 Payer maintenant]({res['url']})")
                        st.caption("Tu seras redirigé vers la page sécurisée CinetPay "
                                   "(Mobile Money ou carte).")
                else:
                    st.error(res["message"])

    if st.button("← Retour"):
        st.session_state.show_premium = False
        st.rerun()
    return True
