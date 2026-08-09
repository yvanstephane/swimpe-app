# =============================================================================
# eligibilite.py — Règles d'ADMISSIBILITÉ par destination × type de projet
# Gérées par l'ADMIN (expertise immigration — aucune API ne fournit cela).
# regle : "TOUS" | "CM,GA,SN" (liste ouverte) | "SAUF:DZ,MA" (tous sauf)
# type  : 'stage' | 'emploi' | 'metier' | '*' (tous les types)
# note  : explication visa affichée au visiteur
# =============================================================================
import streamlit as st
import sqlite3

DB = "data/mobilite.db"
TYPES = ["stage", "emploi", "metier", "*"]


def _init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS eligibilite(
        destination TEXT, type TEXT, regle TEXT DEFAULT 'TOUS',
        note TEXT DEFAULT '', statut TEXT DEFAULT 'a_verifier',
        PRIMARY KEY(destination, type))""")
    con.commit(); con.close()


def autorise(dest_code, type_p, code_orig):
    """(ok, note). Sans règle définie : ouvert par défaut (l'admin restreint)."""
    _init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM eligibilite WHERE destination=? AND type=?",
                      (dest_code.upper(), type_p)).fetchone()
    if not row:
        row = con.execute("SELECT * FROM eligibilite WHERE destination=? AND type='*'",
                          (dest_code.upper(),)).fetchone()
    con.close()
    if not row:
        return True, ""
    regle = (row["regle"] or "TOUS").strip().upper()
    note = row["note"] or ""
    o = (code_orig or "").strip().upper()
    if regle == "TOUS":
        return True, note
    if regle.startswith("SAUF:"):
        exclus = [c.strip() for c in regle[5:].split(",") if c.strip()]
        return (o not in exclus), note
    inclus = [c.strip() for c in regle.split(",") if c.strip()]
    return (o in inclus), note


def definir(dest_code, type_p, regle, note=""):
    _init()
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO eligibilite VALUES(?,?,?,?, 'a_verifier')",
                (dest_code.upper(), type_p, regle.strip().upper() or "TOUS", note.strip()))
    con.commit(); con.close()


def supprimer(dest_code, type_p):
    _init()
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM eligibilite WHERE destination=? AND type=?",
                (dest_code.upper(), type_p))
    con.commit(); con.close()


def _destinations():
    con = sqlite3.connect(DB)
    try:
        rows = con.execute("SELECT code, nom FROM destinations ORDER BY nom").fetchall()
    except sqlite3.Error:
        rows = []
    con.close()
    return rows


def ecran():
    """Écran admin des règles d'admissibilité. True si affiché."""
    if not st.session_state.get("show_eligibilite"):
        return False
    st.markdown("## 🛂 Règles d'admissibilité (par destination)")
    st.caption("Qui peut candidater, selon le pays d'origine. « TOUS » = ouvert ; "
               "« CM,GA,SN » = seulement ces pays ; « SAUF:DZ » = tous sauf ceux-là. "
               "La note visa est montrée au visiteur.")

    _init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    regles = con.execute("SELECT * FROM eligibilite ORDER BY destination, type").fetchall()
    con.close()
    if regles:
        st.markdown("#### Règles existantes")
        for r in regles:
            c1, c2, c3, c4 = st.columns([2, 2, 4, 1])
            c1.markdown(f"**{r['destination']}** · {r['type']}")
            c2.code(r["regle"], language=None)
            c3.caption(r["note"] or "—")
            if c4.button("🗑", key=f"el_del_{r['destination']}_{r['type']}"):
                supprimer(r["destination"], r["type"]); st.rerun()
    else:
        st.info("Aucune règle : tout est ouvert par défaut. Ajoute des restrictions ci-dessous.")

    st.markdown("#### ➕ Ajouter / modifier une règle")
    dests = _destinations()
    with st.form("el_new"):
        c1, c2 = st.columns(2)
        if dests:
            dsel = c1.selectbox("Destination", [f"{c} — {n}" for c, n in dests])
            dest = dsel.split(" — ")[0]
        else:
            dest = c1.text_input("Code destination (ex : CA)")
        type_p = c2.selectbox("Type de projet", TYPES,
                              format_func=lambda x: {"stage": "Stage", "emploi": "Emploi",
                                                     "metier": "Métiers spécialisés",
                                                     "*": "Tous les types"}[x])
        regle = st.text_input("Règle", value="TOUS",
                              help="TOUS · ou liste : CM,GA,SN · ou exclusion : SAUF:DZ,MA")
        note = st.text_input("Note visa (montrée au visiteur)",
                             placeholder="ex : Permis de travail coop requis — délai 8 à 16 semaines")
        ok = st.form_submit_button("Enregistrer", type="primary")
        if ok and dest:
            definir(dest, type_p, regle, note)
            st.success("Règle enregistrée."); st.rerun()

    st.divider()
    if st.button("← Retour", key="el_retour"):
        st.session_state.show_eligibilite = False
        st.rerun()
    return True
