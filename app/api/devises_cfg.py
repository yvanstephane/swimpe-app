# =============================================================================
# devises_cfg.py — Devise d'affichage visiteur (base EUR)
# - Sélecteur manuel dans la sidebar (EUR par défaut)
# - Conversion arrondie à la CENTAINE la plus proche en devise locale
# - Écran admin pour activer/désactiver les devises proposées
# =============================================================================
import streamlit as st
import sqlite3

DB = "data/mobilite.db"

TAUX_DEFAUT = {"EUR":1.0,"USD":1.08,"XOF":655.96,"XAF":655.96,"CAD":1.47,"GBP":0.85,
               "MAD":10.8,"TND":3.4,"NGN":1650,"GHS":16,"KES":140,"HTG":145,"INR":92,
               "PKR":300,"IDR":17500,"BRL":6.0,"RWF":1420,"CDF":2900,"EGP":52,"ZAR":19.5}


def _init(taux=None):
    taux = taux or TAUX_DEFAUT
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS config_devises(code TEXT PRIMARY KEY, actif INT DEFAULT 1)")
    for c in taux:
        con.execute("INSERT OR IGNORE INTO config_devises VALUES(?,1)", (c,))
    con.commit(); con.close()


def actives(taux=None):
    taux = taux or TAUX_DEFAUT
    _init(taux)
    con = sqlite3.connect(DB)
    rows = [r[0] for r in con.execute("SELECT code FROM config_devises WHERE actif=1")]
    con.close()
    act = [c for c in taux if c in rows]
    if "EUR" not in act:
        act.insert(0, "EUR")     # l'euro (base) est toujours disponible
    return act


def devise_courante():
    return st.session_state.get("devise", "EUR")


def selecteur_sidebar(taux=None):
    """Sélecteur de devise dans la sidebar (EUR par défaut)."""
    taux = taux or TAUX_DEFAUT
    opts = actives(taux)
    cur = devise_courante()
    if cur not in opts:
        cur = "EUR"
    choix = st.selectbox("💱 Devise", opts, index=opts.index(cur), key="sel_devise")
    if choix != st.session_state.get("devise"):
        st.session_state.devise = choix


SYMBOLES = {"EUR": ("", " €"), "USD": ("$", ""), "GBP": ("£", ""),
            "CAD": ("", " $ CA"), "BRL": ("R$ ", "")}


def prix_affiche(montant_eur, taux=None, avec_equivalent=False):
    """Format « plateforme d'admission » : montant en devise choisie avec le
    bon symbole. Arrondi à la centaine pour les montants locaux >= 1 000
    (FCFA, NGN...), à l'unité pour les devises fortes (USD, GBP...).
    avec_equivalent=True ajoute « · ≈ X € » quand la devise n'est pas l'euro."""
    taux = taux or TAUX_DEFAUT
    dev = devise_courante()
    eur = round(float(montant_eur))
    eur_txt = f"{eur:,} €".replace(",", " ")
    if dev == "EUR" or dev not in taux:
        return eur_txt
    local = float(montant_eur) / taux["EUR"] * taux[dev]
    if local >= 1000:
        val = int(round(local / 100.0) * 100)
    else:
        val = int(round(local))
    pre, post = SYMBOLES.get(dev, ("", f" {dev}"))
    local_txt = f"{pre}{val:,}{post}".replace(",", " ")
    if avec_equivalent:
        return f"{local_txt} · ≈ {eur_txt}"
    return local_txt


def ecran_admin(taux=None):
    """Écran admin : activer/désactiver les devises. True si affiché."""
    taux = taux or TAUX_DEFAUT
    if not st.session_state.get("show_devises"):
        return False
    st.markdown("## 💱 Devises proposées aux visiteurs")
    st.caption("L'euro (base) est toujours disponible. Coche les devises "
               "locales proposées dans le sélecteur.")
    _init(taux)
    con = sqlite3.connect(DB)
    etat = dict(con.execute("SELECT code, actif FROM config_devises"))
    con.close()
    for c in taux:
        if c == "EUR":
            st.checkbox(f"{c} (base — toujours active)", value=True,
                        disabled=True, key=f"dv_{c}")
            continue
        cur = bool(etat.get(c, 1))
        nv = st.checkbox(c, value=cur, key=f"dv_{c}")
        if nv != cur:
            con = sqlite3.connect(DB)
            con.execute("INSERT OR REPLACE INTO config_devises VALUES(?,?)",
                        (c, 1 if nv else 0))
            con.commit(); con.close()
            st.rerun()
    st.divider()
    if st.button("← Retour", key="dv_retour"):
        st.session_state.show_devises = False
        st.rerun()
    return True
