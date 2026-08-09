# =============================================================================
# offres_cfg.py — Forfaits Premium configurables par l'admin (base EUR)
# Table config_offres(code, label, prix_eur, jours, actif).
# Au premier passage : initialisée depuis paiement.OFFRES (FCFA → EUR).
# CRUD complet : créer, modifier, désactiver, supprimer.
# =============================================================================
import streamlit as st
import sqlite3

DB = "data/mobilite.db"
R = 655.96   # FCFA / EUR


def _init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS config_offres(
        code TEXT PRIMARY KEY, label TEXT, prix_eur REAL,
        jours INT, actif INT DEFAULT 1)""")
    n = con.execute("SELECT COUNT(*) FROM config_offres").fetchone()[0]
    if n == 0:
        try:
            import paiement
            for code, (label, prix, jours) in paiement.OFFRES.items():
                prix_eur = round(prix / R) if prix > 500 else prix
                con.execute("INSERT OR IGNORE INTO config_offres VALUES(?,?,?,?,1)",
                            (code, label, prix_eur, jours))
        except Exception:
            pass
    con.commit(); con.close()


def toutes(actives_seulement=True):
    """{code: (label, prix_eur, jours)} — triées par durée."""
    _init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    q = "SELECT * FROM config_offres" + (" WHERE actif=1" if actives_seulement else "")
    rows = con.execute(q + " ORDER BY jours").fetchall()
    con.close()
    return {r["code"]: (r["label"], float(r["prix_eur"]), int(r["jours"])) for r in rows}


def definir(code, label, prix_eur, jours, actif=1):
    _init()
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO config_offres VALUES(?,?,?,?,?)",
                (code.strip(), label.strip(), float(prix_eur), int(jours), 1 if actif else 0))
    con.commit(); con.close()


def supprimer(code):
    _init()
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM config_offres WHERE code=?", (code,))
    con.commit(); con.close()


def ecran():
    """Écran admin CRUD des offres Premium. True si affiché."""
    if not st.session_state.get("show_offres"):
        return False
    st.markdown("## 💎 Offres Premium (EUR)")
    st.caption("Crée, modifie, désactive ou supprime les forfaits. "
               "Les prix sont en euros ; l'affichage visiteur convertit "
               "dans la devise choisie (arrondi à la centaine locale).")

    for code, (label, prix, jours) in toutes(actives_seulement=False).items():
        with st.expander(f"{label}  ·  {prix:g} €  ·  {jours} j", expanded=False):
            n_label = st.text_input("Libellé", value=label, key=f"of_l_{code}")
            c1, c2, c3 = st.columns(3)
            n_prix = c1.number_input("Prix (€)", min_value=0.0, step=1.0,
                                     value=float(prix), key=f"of_p_{code}")
            n_jours = c2.number_input("Durée (jours)", min_value=1, step=1,
                                      value=int(jours), key=f"of_j_{code}")
            con = sqlite3.connect(DB)
            act = con.execute("SELECT actif FROM config_offres WHERE code=?",
                              (code,)).fetchone()
            con.close()
            n_actif = c3.toggle("Proposée", value=bool(act and act[0]),
                                key=f"of_a_{code}")
            b1, b2 = st.columns(2)
            if b1.button("💾 Enregistrer", key=f"of_s_{code}"):
                definir(code, n_label, n_prix, n_jours, n_actif)
                st.success("Enregistré."); st.rerun()
            cle_del = f"of_del_{code}"
            if st.session_state.get(cle_del):
                if b2.button("⚠️ Confirmer la suppression", key=f"of_d2_{code}",
                             type="primary"):
                    supprimer(code); st.session_state[cle_del] = False; st.rerun()
            else:
                if b2.button("🗑 Supprimer", key=f"of_d_{code}"):
                    st.session_state[cle_del] = True; st.rerun()

    st.divider()
    st.markdown("#### ➕ Nouvelle offre")
    with st.form("of_new"):
        c0, c1, c2, c3 = st.columns([2, 3, 2, 2])
        nc = c0.text_input("Code (unique)")
        nl = c1.text_input("Libellé")
        np = c2.number_input("Prix (€)", min_value=0.0, step=1.0, value=10.0)
        nj = c3.number_input("Jours", min_value=1, step=1, value=30)
        ok = st.form_submit_button("Créer", type="primary")
        if ok:
            if not nc.strip() or not nl.strip():
                st.error("Code et libellé obligatoires.")
            elif nc.strip() in toutes(actives_seulement=False):
                st.error("Ce code existe déjà.")
            else:
                definir(nc, nl, np, nj, 1)
                st.success("Offre créée."); st.rerun()

    st.divider()
    if st.button("← Retour", key="of_retour"):
        st.session_state.show_offres = False
        st.rerun()
    return True
