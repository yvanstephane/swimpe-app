# =============================================================================
# suivi_local.py — Suivi LOCAL des candidatures (Swimpe)
# -----------------------------------------------------------------------------
# Accompagne le jeune sur une offre locale (emploi / stage / concours / formation) :
#   - sa candidature (4 étapes : repérée → dossier → déposée → réponse)
#   - son dossier (pièces à fournir, état de chacune)
#   - un bouton « Demander un conseil » (activable/désactivable dans l'admin)
#
# Règles anti-arnaque respectées :
#   - la liste des pièces part d'un socle universel + s'adapte au TYPE d'offre,
#     et porte toujours la mention « à confirmer sur l'avis officiel » ;
#   - rien n'est présenté comme « source vérifiée » automatiquement : une offre
#     ajoutée par le jeune démarre en « à vérifier » (jamais en vert).
#
# Importé par ui.py (patch_suivi). Utilise sqlite3.connect() que ui.py route
# déjà vers SQLite (local) ou PostgreSQL/Supabase (en ligne).
# =============================================================================
import streamlit as st
import sqlite3
import datetime
import os

# Localisation robuste de la base : on vise d'abord data/mobilite.db à la
# racine du projet (deux dossiers au-dessus de app/api), puis le dossier
# courant, puis le chemin relatif historique. En ligne (Supabase), ce chemin
# est de toute façon ignoré : sqlite3.connect est redirigé vers PostgreSQL.
_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.dirname(os.path.dirname(_ICI))  # app/api -> app -> racine
_CANDIDATS = [
    os.path.join(_RACINE, "data", "mobilite.db"),
    os.path.join(os.getcwd(), "data", "mobilite.db"),
    "data/mobilite.db",
]
DB = next((p for p in _CANDIDATS if os.path.exists(p)), _CANDIDATS[0])

# 4 étapes de la candidature (locale : pas de visa)
ETAPES = ["Offre repérée", "Préparer le dossier", "Candidature déposée", "Entretien / réponse"]

# États possibles d'une pièce
ETATS = ["à fournir", "en cours", "fourni", "validé"]

# Types d'offre proposés à la création
TYPES = ["Emploi", "Stage", "Concours", "Formation", "Volontariat", "Autre"]


def _pieces_par_defaut(type_offre):
    """Socle universel + pièces typiques selon le type. JAMAIS une liste
    inventée pour un employeur précis : à confirmer sur l'avis officiel."""
    socle = ["Pièce d'identité (CNI)", "CV à jour"]
    t = (type_offre or "").strip().lower()
    if t == "concours":
        return socle + ["Lettre de motivation", "Diplômes / attestations",
                        "Extrait de naissance", "Casier judiciaire",
                        "Reçu de paiement (Trésor public)"]
    if t == "formation":
        return socle + ["Lettre de motivation", "Diplômes / relevés de notes"]
    if t in ("emploi", "stage"):
        return socle + ["Lettre de motivation", "Diplômes / attestations"]
    return socle + ["Lettre de motivation"]


# ----------------------------------------------------------------------------
# Base de données (tables créées à la volée, idempotent, SQLite + PostgreSQL)
# ----------------------------------------------------------------------------
def _init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS candidatures(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, date TEXT, titre TEXT, lieu TEXT, type TEXT,
        lien TEXT, date_limite TEXT, etape INTEGER DEFAULT 0,
        source_ok INTEGER DEFAULT 0)""")
    con.execute("""CREATE TABLE IF NOT EXISTS pieces(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cand_id INTEGER, nom TEXT, etat TEXT DEFAULT 'à fournir')""")
    # filet de sécurité : la table leads existe déjà (créée par ui.py), mais on
    # la garantit pour que « Demander un conseil » ne casse jamais.
    con.execute("""CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, nom TEXT, contact TEXT,
        origine TEXT, destination TEXT, service TEXT, message TEXT)""")
    con.commit()
    con.close()


def creer_candidature(user_id, titre, lieu, type_offre, lien, date_limite):
    _init()
    con = sqlite3.connect(DB)
    cur = con.execute(
        "INSERT INTO candidatures(user_id,date,titre,lieu,type,lien,date_limite,etape,source_ok) "
        "VALUES(?,?,?,?,?,?,?,?,?)",
        (user_id, datetime.date.today().isoformat(), titre, lieu, type_offre,
         lien, date_limite, 0, 0))
    cand_id = cur.lastrowid
    for nom in _pieces_par_defaut(type_offre):
        con.execute("INSERT INTO pieces(cand_id,nom,etat) VALUES(?,?,?)",
                    (cand_id, nom, "à fournir"))
    con.commit()
    con.close()
    return cand_id


def mes_candidatures(user_id):
    _init()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM candidatures WHERE user_id=? ORDER BY id DESC",
                       (user_id,)).fetchall()
    con.close()
    return rows


def pieces_de(cand_id):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM pieces WHERE cand_id=? ORDER BY id", (cand_id,)).fetchall()
    con.close()
    return rows


def maj_etape(cand_id, etape):
    con = sqlite3.connect(DB)
    con.execute("UPDATE candidatures SET etape=? WHERE id=?", (int(etape), cand_id))
    con.commit()
    con.close()


def maj_piece(piece_id, etat):
    con = sqlite3.connect(DB)
    con.execute("UPDATE pieces SET etat=? WHERE id=?", (etat, piece_id))
    con.commit()
    con.close()


def supprimer_candidature(cand_id):
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM pieces WHERE cand_id=?", (cand_id,))
    con.execute("DELETE FROM candidatures WHERE id=?", (cand_id,))
    con.commit()
    con.close()


def enregistrer_conseil(user, cand):
    """Enregistre une demande de conseil dans la table leads → visible dans
    l'admin (liste « Demandes clients »), marquée 🆘."""
    _init()
    nom = (user["nom"] if "nom" in user.keys() else None) or ""
    email = user["email"] if "email" in user.keys() else ""
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO leads(date,nom,contact,origine,destination,service,message) "
        "VALUES(?,?,?,?,?,?,?)",
        (datetime.date.today().isoformat(), nom, email, "", cand["lieu"] or "",
         "🆘 Conseil", f"Suivi : {cand['titre']} ({cand['type']})"))
    con.commit()
    con.close()


def _conseil_actif():
    """Lit l'interrupteur admin (défaut : désactivé)."""
    try:
        import offres_sync
        return offres_sync.param("conseil_actif", "0") != "0"
    except Exception:
        return False


def _est_admin():
    """Vrai si l'utilisateur courant est admin (le bouton conseil lui est caché)."""
    try:
        import espace
        return espace.est_admin()
    except Exception:
        return False


def _demandes_conseil():
    """Toutes les demandes de conseil enregistrées, les plus récentes d'abord."""
    _init()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT date,nom,contact,destination,message FROM leads "
            "WHERE service LIKE ? ORDER BY id DESC", ("%Conseil%",)).fetchall()
    except Exception:
        rows = []
    con.close()
    return rows


def bandeau_admin():
    """Bandeau en haut de l'admin : alerte sur les demandes de conseil.
    Montre le total + les plus récentes ; toutes les autres sont dépliables."""
    if not _est_admin():
        return
    demandes = _demandes_conseil()
    if not demandes:
        return
    st.warning(f"🆘 **{len(demandes)} demande(s) de conseil** à traiter.")
    for d in demandes[:3]:
        qui = d["nom"] or d["contact"] or "—"
        lieu = (" · " + d["destination"]) if d["destination"] else ""
        st.markdown(f"- **{qui}**{lieu} · {d['date']}")
    if len(demandes) > 3:
        with st.expander(f"Voir toutes les demandes ({len(demandes)})"):
            for d in demandes:
                qui = d["nom"] or d["contact"] or "—"
                lieu = (" · " + d["destination"]) if d["destination"] else ""
                msg = (" — " + d["message"]) if d["message"] else ""
                st.markdown(f"- **{qui}**{lieu} · {d['date']}{msg}")


# ----------------------------------------------------------------------------
# Écran « Mon suivi »
# ----------------------------------------------------------------------------
def ecran(user):
    if not st.session_state.get("show_suivi"):
        return False

    uid = user["id"]
    nom = (user["nom"] if "nom" in user.keys() else None) or (user["email"] if "email" in user.keys() else "")
    st.markdown(f"## 🗂 Mon suivi — {nom}")
    st.caption("Suivez vos candidatures locales : vos étapes, votre dossier, et demandez un conseil quand vous êtes bloqué·e.")

    # --- Ajouter une candidature ---
    with st.expander("➕ Suivre une nouvelle offre", expanded=False):
        with st.form("form_candidature"):
            titre = st.text_input("Intitulé de l'offre", placeholder="Ex. : Assistant administratif")
            c1, c2 = st.columns(2)
            lieu = c1.text_input("Lieu", placeholder="Ex. : Douala")
            type_offre = c2.selectbox("Type", TYPES)
            lien = st.text_input("Lien de l'offre (facultatif)", placeholder="https://…")
            date_limite = st.text_input("Date limite (facultatif)", placeholder="Ex. : 30 oct.")
            if st.form_submit_button("Ajouter à mon suivi", type="primary", use_container_width=True):
                if titre.strip():
                    creer_candidature(uid, titre.strip(), lieu.strip(), type_offre,
                                      lien.strip(), date_limite.strip())
                    st.success("Candidature ajoutée à votre suivi.")
                    st.rerun()
                else:
                    st.error("Indiquez au moins l'intitulé de l'offre.")

    cands = mes_candidatures(uid)
    if not cands:
        st.info("Vous ne suivez encore aucune offre. Cliquez sur « ➕ Suivre une nouvelle offre » pour commencer.")
    else:
        for cand in cands:
            with st.container(border=True):
                # En-tête de l'offre
                haut = st.columns([4, 1])
                haut[0].markdown(f"**{cand['titre']}**" + (f" · {cand['lieu']}" if cand['lieu'] else ""))
                badges = []
                if cand["lien"]:
                    badges.append("🟡 source à vérifier")
                if cand["date_limite"]:
                    badges.append(f"🗓 {cand['date_limite']}")
                if badges:
                    haut[0].caption(" · ".join(badges))
                if cand["lien"]:
                    haut[0].markdown(f"[Voir l'offre]({cand['lien']})")

                # Ma candidature : les 4 étapes
                st.markdown("**Ma candidature**")
                etape = st.radio("Où en êtes-vous ?", ETAPES, index=int(cand["etape"] or 0),
                                 key=f"etape_{cand['id']}", horizontal=True,
                                 label_visibility="collapsed")
                if ETAPES.index(etape) != int(cand["etape"] or 0):
                    maj_etape(cand["id"], ETAPES.index(etape))
                    st.rerun()

                # Mon dossier : les pièces
                pieces = pieces_de(cand["id"])
                faits = sum(1 for p in pieces if p["etat"] in ("fourni", "validé"))
                st.markdown(f"**Mon dossier** — {faits} / {len(pieces)} pièces")
                st.caption("🛡 Liste de départ, à confirmer sur l'avis officiel de l'offre — jamais inventée.")
                for p in pieces:
                    cols = st.columns([3, 2])
                    cols[0].write(p["nom"])
                    etat = cols[1].selectbox("état", ETATS, index=ETATS.index(p["etat"]) if p["etat"] in ETATS else 0,
                                             key=f"piece_{p['id']}", label_visibility="collapsed")
                    if etat != p["etat"]:
                        maj_piece(p["id"], etat)
                        st.rerun()

                # Accompagnement : bouton conseil (si activé dans l'admin,
                # et jamais montré à l'admin lui-même : il reçoit, il ne demande pas)
                if _conseil_actif() and not _est_admin():
                    if st.button("🆘 Demander un conseil", key=f"conseil_{cand['id']}",
                                 use_container_width=True):
                        enregistrer_conseil(user, cand)
                        st.success("Votre demande de conseil a été transmise à l'équipe Swimpe. On revient vers vous.")

                # Retirer
                if st.button("🗑 Retirer cette offre", key=f"del_{cand['id']}"):
                    supprimer_candidature(cand["id"])
                    st.rerun()

    st.divider()
    if st.button("← Retour"):
        st.session_state.show_suivi = False
        st.rerun()
    return True
