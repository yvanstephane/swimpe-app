# =============================================================================
# dossiers.py — Suivi des démarches déléguées Yorbity
# Côté étudiant : "Mes démarches" avec barre de progression.
# Côté admin : gestion de tous les dossiers (statut, notes internes, notes client).
# =============================================================================
import streamlit as st
import sqlite3, datetime
from i18n import t

DB = "data/mobilite.db"

def _lg():
    return st.session_state.get("lang", "fr")

# Statuts ordonnés = les étapes de vie d'un dossier
STATUTS = [
    ("recu", "statut_recu", 5), ("analyse", "statut_analyse", 20),
    ("en_cours", "statut_en_cours", 45), ("documents", "statut_documents", 60),
    ("soumis", "statut_soumis", 85), ("termine", "statut_termine", 100),
]
def statut_label(code):
    cle = dict((c, k) for c, k, _ in STATUTS).get(code, code)
    return t(cle, _lg())
STATUT_LABEL = {c: k for c, k, _ in STATUTS}
STATUT_PCT   = {c: p for c, _, p in STATUTS}

def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS dossiers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        service TEXT,
        destination TEXT,
        statut TEXT DEFAULT 'recu',
        note_client TEXT DEFAULT '',
        note_interne TEXT DEFAULT '',
        cree_le TEXT,
        maj_le TEXT)""")
    con.commit(); con.close()

def creer(user_id, service, destination, beneficiaire=None,
          autorise_tiers=False):
    """Cree LE dossier du compte — un seul dossier par client
    (patch_langue_dossier). Les candidatures du client s'y rattachent.
    `autorise_tiers=True` (ecrans admin) passe outre.
    Retourne (True, "") ou (False, message). Le refus est aussi affiche a
    l'ecran quand Streamlit est disponible : pas d'echec silencieux."""
    init_db()
    con = sqlite3.connect(DB)
    try:
        row = con.execute("SELECT nom FROM users WHERE id=?",
                          (user_id,)).fetchone()
        if not row:
            return _refus("Compte introuvable.")
        if not autorise_tiers:
            deja = con.execute(
                "SELECT id, service, destination FROM dossiers "
                "WHERE user_id=? ORDER BY id LIMIT 1", (user_id,)).fetchone()
            if deja:
                return _refus(
                    "Un seul dossier par compte : le tien est le "
                    f"n°{deja[0]} ({deja[1]} → {deja[2]}). Tes candidatures "
                    "s'y rattachent — contacte-nous pour le faire evoluer.")
        auj = datetime.date.today().isoformat()
        con.execute("INSERT INTO dossiers(user_id,service,destination,cree_le,maj_le) "
                    "VALUES(?,?,?,?,?)", (user_id, service, destination, auj, auj))
        con.commit()
        return True, ""
    finally:
        con.close()


def _refus(msg):
    try:
        import streamlit as _st
        _st.warning("🗂 " + msg)
    except Exception:
        pass
    return False, msg
def liste_user(user_id):
    init_db()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM dossiers WHERE user_id=? ORDER BY id DESC",
                       (user_id,)).fetchall()
    con.close()
    return [dict(r) for r in rows]

def liste_tous():
    init_db()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("""SELECT d.*, u.nom AS client_nom, u.email AS client_email,
                                 u.telephone AS client_tel
                          FROM dossiers d LEFT JOIN users u ON u.id = d.user_id
                          ORDER BY CASE d.statut WHEN 'termine' THEN 1 ELSE 0 END,
                                   d.maj_le DESC""").fetchall()
    con.close()
    return [dict(r) for r in rows]

def maj(dossier_id, statut=None, note_client=None, note_interne=None):
    con = sqlite3.connect(DB)
    if statut is not None:
        con.execute("UPDATE dossiers SET statut=?, maj_le=? WHERE id=?",
                    (statut, datetime.date.today().isoformat(), dossier_id))
    if note_client is not None:
        con.execute("UPDATE dossiers SET note_client=?, maj_le=? WHERE id=?",
                    (note_client, datetime.date.today().isoformat(), dossier_id))
    if note_interne is not None:
        con.execute("UPDATE dossiers SET note_interne=? WHERE id=?",
                    (note_interne, dossier_id))
    con.commit(); con.close()

# =============================================================================
# ÉCRAN ÉTUDIANT — "Mes démarches"
# =============================================================================
def ecran_mes_demarches(user):
    if not st.session_state.get("show_demarches"):
        return False
    st.markdown("## " + t("demarches", _lg()))
    ds = liste_user(user["id"])
    if not ds:
        st.info(t("aucune_demarche", _lg()))
    for d in ds:
        pct = STATUT_PCT.get(d["statut"], 5)
        label = statut_label(d["statut"])
        with st.container(border=True):
            st.markdown(f"**{d['service']}** → {d['destination']}")
            st.progress(pct / 100, text=f"{label} · {pct} %")
            if d["note_client"]:
                st.info(t("msg_equipe", _lg()) + " " + d["note_client"])
            st.caption(f"{t('ouvert_le', _lg())} {d['cree_le']} · {t('maj_le', _lg())} {d['maj_le']}")
    if st.button("← " + t("btn_retour", _lg())):
        st.session_state.show_demarches = False
        st.rerun()
    return True

# =============================================================================
# ÉCRAN ADMIN — gestion de tous les dossiers
# =============================================================================
def ecran_admin():
    if not st.session_state.get("show_gestion"):
        return False
    st.markdown("## 🛠 Gestion des dossiers (admin)")
    ds = liste_tous()
    if not ds:
        st.info("Aucun dossier pour l'instant.")
    actifs = [d for d in ds if d["statut"] != "termine"]
    termines = [d for d in ds if d["statut"] == "termine"]
    st.caption(f"{len(actifs)} dossier(s) actif(s) · {len(termines)} terminé(s)")

    codes = [c for c, _, _ in STATUTS]
    for d in ds:
        label = statut_label(d["statut"])
        titre = (f"#{d['id']} · {d['service']} → {d['destination']} · "
                 f"{d.get('client_nom') or '?'} · {label}")
        with st.expander(titre, expanded=(d["statut"] == "recu")):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Client :** {d.get('client_nom') or '—'}  \n"
                        f"**Contact :** {d.get('client_email') or '—'} · "
                        f"{d.get('client_tel') or ''}")
            c2.markdown(f"**Ouvert :** {d['cree_le']}  \n**Maj :** {d['maj_le']}")

            nouveau_statut = st.selectbox(
                "Statut", codes,
                index=codes.index(d["statut"]) if d["statut"] in codes else 0,
                format_func=lambda c: statut_label(c),
                key=f"st_{d['id']}")
            note_c = st.text_input("Message visible par le client",
                                   value=d["note_client"] or "", key=f"nc_{d['id']}")
            note_i = st.text_area("Note interne (jamais visible client)",
                                  value=d["note_interne"] or "", key=f"ni_{d['id']}",
                                  height=68)
            if st.button("💾 Enregistrer", key=f"sv_{d['id']}"):
                maj(d["id"], statut=nouveau_statut,
                    note_client=note_c, note_interne=note_i)
                st.success("Enregistré.")
                st.rerun()
    if st.button("← Retour "):
        st.session_state.show_gestion = False
        st.rerun()
    return True
