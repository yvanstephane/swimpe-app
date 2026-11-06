# =============================================================================
# posts_facebook_ui.py — Écran admin « Posts Facebook » (générateur Swimpe)
# -----------------------------------------------------------------------------
# Gère la table posts_facebook : lister, créer à la main, modifier les textes,
# faire avancer le statut (brouillon → validé → publié) et supprimer.
# Chaque post reprend la mécanique des pages virales (Yaya) mais pointe vers
# une fonction de la plateforme Swimpe. swimpe.com va dans l'image, le lien
# cliquable dans le 1er commentaire.
#
# Accès réservé à l'admin (le dispatch dans ui.py enveloppe déjà d'un
# espace.est_admin()). La table est protégée côté base par est_admin() (RLS).
# =============================================================================
import streamlit as st
import sqlite3
import datetime

DB = "data/mobilite.db"

try:
    import carte_image
except Exception:
    carte_image = None


@st.cache_data(show_spinner=False)
def _png(carte_texte):
    """Image PNG de la carte (en cache tant que le texte ne change pas)."""
    if carte_image is None or not carte_texte:
        return None
    try:
        return carte_image.generer_png(carte_texte)
    except Exception:
        return None


# Valeurs alignées sur les contraintes CHECK de la table posts_facebook.
STATUTS = ["brouillon", "valide", "publie"]
BADGE_STATUT = {"brouillon": "✏️ Brouillon", "valide": "✅ Validé", "publie": "📣 Publié"}
REGISTRES = ["juste_milieu", "senegal", "chretien"]
LABEL_REGISTRE = {
    "juste_milieu": "Juste milieu (tous)",
    "senegal": "Sénégal (inchallah)",
    "chretien": "Chrétien (Seigneur)",
}
# Pays : None = tous. Codes alignés sur offres_locales (CM / SN / CI).
PAYS = [None, "CM", "SN", "CI"]
LABEL_PAYS = {None: "🌍 Tous", "CM": "🇨🇲 Cameroun", "SN": "🇸🇳 Sénégal", "CI": "🇨🇮 Côte d'Ivoire"}


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _lister(filtre_statut=None):
    """Retourne les posts (plus récents d'abord), filtrés par statut si demandé."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        if filtre_statut and filtre_statut in STATUTS:
            rows = con.execute(
                "SELECT * FROM posts_facebook WHERE statut=? "
                "ORDER BY cree_le DESC", (filtre_statut,)).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM posts_facebook ORDER BY cree_le DESC").fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        st.error(f"Lecture impossible : {e}")
        return []
    finally:
        con.close()


def _compter():
    """Compte par statut, pour les métriques en haut d'écran."""
    con = sqlite3.connect(DB)
    try:
        out = {s: 0 for s in STATUTS}
        for statut, n in con.execute(
                "SELECT statut, COUNT(*) FROM posts_facebook GROUP BY statut"):
            out[statut] = n
        return out
    except sqlite3.Error:
        return {s: 0 for s in STATUTS}
    finally:
        con.close()


def _creer(d):
    con = sqlite3.connect(DB)
    try:
        con.execute(
            "INSERT INTO posts_facebook "
            "(mecanique, gabarit, avantage, carte_texte, post_texte, commentaire, "
            " pays, registre, statut) VALUES (?,?,?,?,?,?,?,?,?)",
            (d["mecanique"], d["gabarit"], d["avantage"], d["carte_texte"],
             d["post_texte"], d["commentaire"], d["pays"], d["registre"], "brouillon"))
        con.commit()
        return True, "Post ajouté en brouillon."
    except sqlite3.Error as e:
        return False, f"Enregistrement impossible : {e}"
    finally:
        con.close()


def _maj_textes(pid, carte, post, commentaire, pays, registre):
    con = sqlite3.connect(DB)
    try:
        con.execute(
            "UPDATE posts_facebook SET carte_texte=?, post_texte=?, commentaire=?, "
            "pays=?, registre=?, maj_le=? WHERE id=?",
            (carte, post, commentaire, pays, registre, _now(), pid))
        con.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Modification impossible : {e}")
        return False
    finally:
        con.close()


def _changer_statut(pid, statut):
    con = sqlite3.connect(DB)
    try:
        if statut == "publie":
            con.execute(
                "UPDATE posts_facebook SET statut=?, publie_le=?, maj_le=? WHERE id=?",
                (statut, _now(), _now(), pid))
        else:
            con.execute(
                "UPDATE posts_facebook SET statut=?, maj_le=? WHERE id=?",
                (statut, _now(), pid))
        con.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Changement de statut impossible : {e}")
        return False
    finally:
        con.close()


def _supprimer(pid):
    con = sqlite3.connect(DB)
    try:
        con.execute("DELETE FROM posts_facebook WHERE id=?", (pid,))
        con.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Suppression impossible : {e}")
        return False
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Formulaire « nouveau post »
# ---------------------------------------------------------------------------
def _form_nouveau():
    with st.expander("➕ Nouveau post (à la main)"):
        with st.form("pf_nouveau", clear_on_submit=True):
            carte = st.text_area(
                "Carte (texte sur l'image)",
                placeholder="Tu as postulé partout. Silence total. 😮‍💨",
                help="L'accroche imprimée sur l'image. Pense à y mettre swimpe.com.")
            post = st.text_area(
                "Texte du post",
                placeholder="Ce silence ne dit pas que tu ne vaux rien…")
            commentaire = st.text_input("1er commentaire (le lien)", value="👉 swimpe.com")
            c1, c2 = st.columns(2)
            pays = c1.selectbox("Pays ciblé", PAYS, format_func=lambda p: LABEL_PAYS[p])
            registre = c2.selectbox("Registre", REGISTRES,
                                    format_func=lambda r: LABEL_REGISTRE[r])
            c3, c4 = st.columns(2)
            avantage = c3.text_input("Avantage vendu",
                                     placeholder="Base d'offres vérifiées")
            mecanique = c4.text_input("Mécanique",
                                      placeholder="silence, arnaque, suspense…")
            gabarit = st.number_input("N° de gabarit (0 = aucun)", min_value=0,
                                      max_value=10, value=0, step=1)
            if st.form_submit_button("Ajouter en brouillon", type="primary"):
                if not carte.strip() and not post.strip():
                    st.error("Écris au moins la carte ou le texte du post.")
                else:
                    ok, msg = _creer({
                        "mecanique": mecanique.strip() or None,
                        "gabarit": int(gabarit) or None,
                        "avantage": avantage.strip() or None,
                        "carte_texte": carte.strip() or None,
                        "post_texte": post.strip() or None,
                        "commentaire": commentaire.strip() or "👉 swimpe.com",
                        "pays": pays,
                        "registre": registre,
                    })
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()


# ---------------------------------------------------------------------------
# Édition d'un post existant
# ---------------------------------------------------------------------------
def _bloc_edition(p):
    pid = p["id"]
    with st.form(f"pf_edit_{pid}"):
        carte = st.text_area("Carte (image)", value=p.get("carte_texte") or "",
                             key=f"e_carte_{pid}")
        post = st.text_area("Texte du post", value=p.get("post_texte") or "",
                           key=f"e_post_{pid}")
        commentaire = st.text_input("1er commentaire", value=p.get("commentaire") or "👉 swimpe.com",
                                    key=f"e_com_{pid}")
        c1, c2 = st.columns(2)
        pays_val = p.get("pays")
        pays = c1.selectbox("Pays", PAYS, index=PAYS.index(pays_val) if pays_val in PAYS else 0,
                            format_func=lambda x: LABEL_PAYS[x], key=f"e_pays_{pid}")
        reg_val = p.get("registre") or "juste_milieu"
        registre = c2.selectbox("Registre", REGISTRES,
                                index=REGISTRES.index(reg_val) if reg_val in REGISTRES else 0,
                                format_func=lambda x: LABEL_REGISTRE[x], key=f"e_reg_{pid}")
        cc1, cc2 = st.columns(2)
        if cc1.form_submit_button("💾 Enregistrer", type="primary"):
            if _maj_textes(pid, carte.strip() or None, post.strip() or None,
                           commentaire.strip() or "👉 swimpe.com", pays, registre):
                st.session_state[f"edit_pf_{pid}"] = False
                st.success("Modifié.")
                st.rerun()
        if cc2.form_submit_button("Annuler"):
            st.session_state[f"edit_pf_{pid}"] = False
            st.rerun()


# ---------------------------------------------------------------------------
# Affichage d'un post (lecture + actions)
# ---------------------------------------------------------------------------
def _bloc_post(p):
    pid = p["id"]
    statut = p.get("statut") or "brouillon"
    titre = (p.get("carte_texte") or p.get("post_texte") or "(vide)").strip()
    titre_court = (titre[:70] + "…") if len(titre) > 70 else titre
    drapeau = LABEL_PAYS.get(p.get("pays"), "🌍 Tous").split()[0]

    with st.container(border=True):
        haut = st.columns([6, 2])
        haut[0].markdown(f"{drapeau} **{titre_court}**")
        haut[1].markdown(BADGE_STATUT.get(statut, statut))

        if st.session_state.get(f"edit_pf_{pid}"):
            _bloc_edition(p)
            return

        if p.get("carte_texte"):
            st.markdown("🖼️ *" + p["carte_texte"] + "*")
        if p.get("post_texte"):
            st.markdown("📝 " + p["post_texte"])
        if p.get("commentaire"):
            st.caption("💬 " + p["commentaire"])
        meta = []
        if p.get("avantage"):
            meta.append("🎯 " + p["avantage"])
        if p.get("gabarit"):
            meta.append(f"#{p['gabarit']}")
        meta.append(LABEL_REGISTRE.get(p.get("registre") or "juste_milieu", ""))
        st.caption(" · ".join(x for x in meta if x))

        # ---- Bloc PUBLIER (assisté, depuis le téléphone) ----
        with st.expander("📤 Publier (image · texte · Facebook)"):
            png = _png(p.get("carte_texte") or "")
            if png:
                st.image(png)
                st.download_button("⬇️ Télécharger l'image", png,
                                   file_name=f"swimpe_{str(pid)[:8]}.png",
                                   mime="image/png", key=f"dl_{pid}",
                                   use_container_width=True)
            else:
                st.caption("Image indisponible (Pillow non installé sur le serveur).")
            st.markdown("**1.** Télécharge l'image · **2.** copie le texte · "
                        "**3.** ouvre Facebook, colle + attache l'image, publie · "
                        "**4.** colle le lien en 1er commentaire.")
            if p.get("post_texte"):
                st.caption("📝 Texte du post (appuie sur l'icône copier) :")
                st.code(p["post_texte"], language=None)
            if p.get("commentaire"):
                st.caption("💬 Commentaire à coller (le lien) :")
                st.code(p["commentaire"], language=None)
            st.link_button("📘 Ouvrir Facebook", "https://www.facebook.com/",
                           use_container_width=True)

        # Actions selon le statut
        a = st.columns(4)
        if statut == "brouillon":
            if a[0].button("✅ Valider", key=f"val_{pid}"):
                if _changer_statut(pid, "valide"):
                    st.rerun()
        elif statut == "valide":
            if a[0].button("📣 Marquer publié", key=f"pub_{pid}"):
                if _changer_statut(pid, "publie"):
                    st.rerun()
            if a[1].button("↩️ Brouillon", key=f"ret_{pid}"):
                if _changer_statut(pid, "brouillon"):
                    st.rerun()
        elif statut == "publie":
            if a[0].button("↩️ Repasser en validé", key=f"deval_{pid}"):
                if _changer_statut(pid, "valide"):
                    st.rerun()

        if a[2].button("✏️ Éditer", key=f"edit_btn_{pid}"):
            st.session_state[f"edit_pf_{pid}"] = True
            st.rerun()

        cle_conf = f"conf_del_{pid}"
        if st.session_state.get(cle_conf):
            if a[3].button("⚠️ Confirmer", key=f"go_del_{pid}", type="primary"):
                st.session_state[cle_conf] = False
                if _supprimer(pid):
                    st.rerun()
        else:
            if a[3].button("🗑️ Supprimer", key=f"ask_del_{pid}"):
                st.session_state[cle_conf] = True
                st.rerun()


# ---------------------------------------------------------------------------
# Écran principal
# ---------------------------------------------------------------------------
def ecran():
    """Écran admin des posts Facebook. True s'il est affiché (bloque la page)."""
    if not st.session_state.get("show_posts_fb"):
        return False

    st.markdown("## 📣 Posts Facebook")
    st.caption("Chaque post reprend la mécanique des pages virales mais pointe "
               "vers une fonction de Swimpe. swimpe.com va dans l'image ; le lien "
               "cliquable dans le 1er commentaire. Un post = un seul avantage.")

    cpt = _compter()
    m = st.columns(3)
    m[0].metric("✏️ Brouillons", cpt.get("brouillon", 0))
    m[1].metric("✅ Validés", cpt.get("valide", 0))
    m[2].metric("📣 Publiés", cpt.get("publie", 0))

    _form_nouveau()

    st.divider()
    choix = st.radio("Filtrer", ["Tous"] + [BADGE_STATUT[s] for s in STATUTS],
                     horizontal=True, key="pf_filtre")
    filtre = None
    for s in STATUTS:
        if choix == BADGE_STATUT[s]:
            filtre = s

    posts = _lister(filtre)
    if not posts:
        st.info("Aucun post pour ce filtre. Ajoute-en un ci-dessus, ou l'usine "
                "en déposera automatiquement.")
    else:
        for p in posts:
            _bloc_post(p)

    st.divider()
    if st.button("← Retour", key="pf_retour"):
        st.session_state.show_posts_fb = False
        st.rerun()
    return True
