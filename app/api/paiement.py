# =============================================================================
# paiement.py (v2) — Paiements Yorbity via CinetPay : Premium ET services
# a la carte, devise et canal adaptes au PAYS DU CLIENT.
#
# MODE TEST par defaut : aucun argent ne circule, tout le parcours se valide
# (Premium active, service livre dans le dossier). Passage en REEL =
# CINETPAY_API_KEY + CINETPAY_SITE_ID dans .env et CINETPAY_MODE=reel.
#
# « Le moyen de paiement le plus efficace par endroit » :
#   - Zone XOF (Senegal, Cote d'Ivoire, Mali, Benin, Togo, Burkina, Niger)
#     et zone XAF (Cameroun, Gabon, Tchad, Congo, RCA, Guinee eq.) :
#     Mobile Money + carte (channels ALL) — le guichet CinetPay detecte le
#     pays du payeur et propose ses operateurs locaux (Orange, MTN, Wave...).
#     XOF et XAF sont a parite (655,957 / EUR) : meme montant.
#   - Guinee (GNF) et RDC (CDF) : Mobile Money natif CinetPay, montant
#     converti (taux indicatifs, surchargeables par l'admin :
#     definir_param("taux_eur:GNF", "...")).
#   - Partout ailleurs (Maghreb, Europe, reste du monde) : CARTE BANCAIRE
#     (Visa/Mastercard, disponibles dans tous les pays CinetPay), facturee
#     en XOF avec l'equivalent local affiche en toute transparence.
#
# Limite CinetPay assumee : PAS de paiement recurrent. Le Premium est donc
# un acces prepaye (30/90/365 jours) que le client renouvelle lui-meme —
# c'est deja le modele d'activer_premium(jours).
# =============================================================================
import datetime
import json
import os
import secrets
import sqlite3

DB = "data/mobilite.db"

MODE = os.environ.get("CINETPAY_MODE", "test")        # "test" ou "reel"
API_KEY = os.environ.get("CINETPAY_API_KEY", "")
SITE_ID = os.environ.get("CINETPAY_SITE_ID", "")
BASE_URL = os.environ.get("YORBITY_URL", "http://localhost:8501")

# Offres d'abonnement (prix en FCFA, duree en jours)
OFFRES = {
    "premium_mensuel":   ("⭐ Premium — 1 mois",   5000,   30),
    "premium_trimestre": ("⭐ Premium — 3 mois",  12000,   90),
    "premium_annuel":    ("⭐ Premium — 1 an",    40000,  365),
}

# Services a la carte : injectes au demarrage par ui.py depuis SVC,
# pour ne pas dupliquer le catalogue. {code: (label, prix_fcfa)}
SERVICES: dict = {}


def enregistrer_services(svc: dict) -> None:
    """ui.py appelle : paiement.enregistrer_services(SVC).
    Accepte le format SVC {code: (label, description, prix_fcfa)}."""
    global SERVICES
    SERVICES = {code: (v[0], int(v[2])) for code, v in svc.items()
                if len(v) >= 3 and v[2]}


def duree_jours(code: str) -> int:
    """Jours de Premium accordes par ce code. 0 = service a la carte.
    (Remplace le piege OFFRES.get(code, ('', 0, 30))[2] qui offrait 30 jours
    de Premium a tout code inconnu.)"""
    return OFFRES.get(code, ("", 0, 0))[2]


def _label_montant(code: str):
    if code in OFFRES:
        label, montant, _ = OFFRES[code]
        return label, montant
    if code in SERVICES:
        return SERVICES[code]
    return None, None


# ----------------------------------------------------------------------------
# Devise et canal selon le PAYS DU CLIENT (pays_origine du compte)
# ----------------------------------------------------------------------------
PAYS_CODE = {
    "cameroun": "CM", "senegal": "SN", "sénégal": "SN",
    "cote d'ivoire": "CI", "côte d'ivoire": "CI", "côte d’ivoire": "CI",
    "mali": "ML", "benin": "BJ", "bénin": "BJ", "togo": "TG",
    "burkina faso": "BF", "niger": "NE", "guinee-bissau": "GW",
    "gabon": "GA", "tchad": "TD", "congo (brazzaville)": "CG",
    "centrafrique": "CF", "guinee equatoriale": "GQ",
    "guinee": "GN", "guinée": "GN", "congo (rdc)": "CD",
    "algerie": "DZ", "algérie": "DZ", "maroc": "MA", "tunisie": "TN",
    "nigeria": "NG", "ghana": "GH", "kenya": "KE",
    "france": "FR", "belgique": "BE",
}
_ZONE_XOF = {"SN", "CI", "ML", "BJ", "TG", "BF", "NE", "GW"}
_ZONE_XAF = {"CM", "GA", "TD", "CG", "CF", "GQ"}

# Taux indicatifs pour 1 EUR (surcharge admin : definir_param("taux_eur:GNF"))
_TAUX_EUR = {"GNF": 9500.0, "CDF": 2900.0}
_EUR_XOF = 655.957


def _taux(devise: str) -> float:
    try:
        import offres_sync
        v = offres_sync.param(f"taux_eur:{devise}", "")
        if v:
            return float(str(v).replace(",", "."))
    except Exception:
        pass
    return _TAUX_EUR[devise]


def code_pays(pays_origine_nom: str) -> str:
    return PAYS_CODE.get((pays_origine_nom or "").strip().lower(), "")


def devise_cinetpay(pays_origine_nom: str, montant_fcfa: int):
    """(devise, montant_facture, channels) pour CinetPay, selon le client.
    XOF/XAF : Mobile Money natif, montant identique (parite).
    GNF/CDF : Mobile Money natif, montant converti (arrondi a 100).
    Ailleurs : carte bancaire, facturee en XOF."""
    code = code_pays(pays_origine_nom)
    if code in _ZONE_XOF:
        return "XOF", int(montant_fcfa), "ALL"
    if code in _ZONE_XAF:
        return "XAF", int(montant_fcfa), "ALL"
    if code in ("GN", "CD"):
        devise = "GNF" if code == "GN" else "CDF"
        eur = montant_fcfa / _EUR_XOF
        local = int(round(eur * _taux(devise) / 100.0) * 100)
        return devise, max(100, local), "ALL"
    return "XOF", int(montant_fcfa), "CREDIT_CARD"


def montant_affiche(pays_origine_nom: str, montant_fcfa: int) -> str:
    """Prix dans la devise du pays du client, pour l'AFFICHAGE (devises.py).
    Repli : « N FCFA » si devises indisponible ou pays inconnu."""
    code = code_pays(pays_origine_nom)
    try:
        import devises
        if code:
            p = devises.prix(montant_fcfa / _EUR_XOF, code)
            n = devises.note(montant_fcfa / _EUR_XOF, code)
            return p + ((" · " + n) if n else "")
    except Exception:
        pass
    return f"{montant_fcfa:,}".replace(",", "\u202f") + "\u00a0FCFA"


# ----------------------------------------------------------------------------
# Table des transactions
# ----------------------------------------------------------------------------
def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS paiements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE,
        user_id INTEGER,
        offre TEXT,
        montant INTEGER,
        devise TEXT DEFAULT 'XOF',
        statut TEXT DEFAULT 'en_attente',   -- en_attente / paye / echec
        mode TEXT,
        date TEXT,
        detail TEXT
    )""")
    con.commit(); con.close()


def _nouvelle_transaction(user_id, offre_code, montant, devise="XOF"):
    init_db()
    tid = "YORBITY-" + secrets.token_hex(8).upper()
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO paiements(transaction_id,user_id,offre,montant,devise,statut,mode,date) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (tid, user_id, offre_code, montant, devise, "en_attente", MODE,
                 datetime.datetime.now().isoformat(timespec="seconds")))
    con.commit(); con.close()
    return tid


def _marquer(transaction_id, statut, detail=""):
    con = sqlite3.connect(DB)
    con.execute("UPDATE paiements SET statut=?, detail=? WHERE transaction_id=?",
                (statut, detail, transaction_id))
    con.commit(); con.close()


# ----------------------------------------------------------------------------
# Lancer un paiement (Premium OU service a la carte)
#   - MODE TEST : marque paye immediatement (simulation)
#   - MODE REEL : appelle CinetPay, devise/canal selon le pays du client
# Retour : {ok, mode, transaction_id, url, jours, montant, devise, label, message}
# ----------------------------------------------------------------------------
def lancer_paiement(user, offre_code):
    label, montant_fcfa = _label_montant(offre_code)
    if label is None:
        return {"ok": False, "message": "Offre inconnue."}
    jours = duree_jours(offre_code)
    devise, montant, channels = devise_cinetpay(user.get("pays_origine", ""),
                                                montant_fcfa)
    tid = _nouvelle_transaction(user["id"], offre_code, montant, devise)

    # ---------- MODE TEST ----------
    if MODE != "reel" or not (API_KEY and SITE_ID):
        _marquer(tid, "paye", "SIMULATION (mode test)")
        return {"ok": True, "mode": "test", "transaction_id": tid,
                "url": None, "jours": jours, "montant": montant,
                "devise": devise, "label": label,
                "message": "Mode test : aucun argent ne circule."}

    # ---------- MODE REEL (CinetPay) ----------
    try:
        import urllib.request
        payload = {
            "apikey": API_KEY,
            "site_id": SITE_ID,
            "transaction_id": tid,
            "amount": montant,
            "currency": devise,
            "description": f"Yorbity {label}",
            "customer_name": user.get("nom", ""),
            "customer_email": user.get("email", ""),
            "notify_url": f"{BASE_URL}/?cinetpay_notify=1",
            "return_url": f"{BASE_URL}/?paiement_retour={tid}",
            "channels": channels,
        }
        req = urllib.request.Request(
            "https://api-checkout.cinetpay.com/v2/payment",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        rep = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if rep.get("code") == "201":
            url = rep["data"]["payment_url"]
            return {"ok": True, "mode": "reel", "transaction_id": tid,
                    "url": url, "jours": jours, "montant": montant,
                    "devise": devise, "label": label,
                    "message": "Redirection vers le paiement sécurisé."}
        _marquer(tid, "echec", str(rep))
        return {"ok": False, "message": f"CinetPay: {rep.get('message','erreur')}"}
    except Exception as e:
        _marquer(tid, "echec", str(e))
        return {"ok": False, "message": f"Erreur technique: {e}"}


# ----------------------------------------------------------------------------
# Verifier le statut d'une transaction (retour CinetPay, mode reel)
# ----------------------------------------------------------------------------
def verifier_paiement(transaction_id):
    if MODE != "reel" or not (API_KEY and SITE_ID):
        return "paye"  # test
    try:
        import urllib.request
        payload = {"apikey": API_KEY, "site_id": SITE_ID,
                   "transaction_id": transaction_id}
        req = urllib.request.Request(
            "https://api-checkout.cinetpay.com/v2/payment/check",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        rep = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if rep.get("code") == "00" and rep["data"]["status"] == "ACCEPTED":
            _marquer(transaction_id, "paye", "confirmé CinetPay")
            return "paye"
        return "echec"
    except Exception:
        return "echec"


def offre_de_transaction(transaction_id):
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM paiements WHERE transaction_id=?",
                      (transaction_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def historique(user_id):
    init_db()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM paiements WHERE user_id=? "
                       "ORDER BY id DESC", (user_id,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ----------------------------------------------------------------------------
# LIVRAISON d'un service a la carte : rattache au DOSSIER UNIQUE du client.
#   - pas de dossier -> le paiement CREE le dossier (service = label)
#   - dossier existant -> la ligne est AJOUTEE a la note visible du client
# ----------------------------------------------------------------------------
def livrer_service(info, user):
    """info = ligne de la table paiements ; user = dict du compte connecte.
    Retourne un message affichable."""
    code = info.get("offre", "")
    label = (SERVICES.get(code) or (code, 0))[0]
    tid = info.get("transaction_id", "")
    try:
        import dossiers
        existants = dossiers.liste_user(user["id"])
        ligne = (f"✅ {label} — payé le "
                 f"{datetime.date.today().isoformat()} ({tid})")
        if existants:
            d = existants[0]
            note = (d.get("note_client") or "").strip()
            note = (note + "\n" if note else "") + ligne
            dossiers.maj(d["id"], note_client=note)
            return f"{label} ajouté à ton dossier n°{d['id']}."
        ok, msg = dossiers.creer(user["id"], service=label, destination="")
        if ok:
            return f"Dossier ouvert avec {label} — suis-le dans « Mes démarches »."
        return msg
    except Exception as e:
        return f"{label} payé ({tid}) — notre équipe te contacte. [{e}]"


# ----------------------------------------------------------------------------
# ECRAN « Services & démarches » — boutique a la carte pour client connecte.
# Ouvert par st.session_state.show_boutique (bouton dans la barre laterale).
# Retourne True si l'ecran a ete affiche (ui.py fait alors st.stop()).
# ----------------------------------------------------------------------------
def ecran_boutique(user):
    import streamlit as st
    if not st.session_state.get("show_boutique"):
        return False

    st.markdown("## 🛠 Services & démarches")
    st.caption("Ton abonnement et tes services sont personnels — "
               "ils se rattachent à ton dossier.")
    if MODE != "reel" or not (API_KEY and SITE_ID):
        st.info("🧪 Mode test : aucun argent ne circule — le parcours "
                "complet se valide sans paiement réel.")

    pays = user.get("pays_origine", "")

    st.markdown("#### ⭐ Premium")
    c = st.columns(len(OFFRES))
    for col, (code, (label, montant, jours)) in zip(c, OFFRES.items()):
        with col:
            st.markdown(f"**{label}**")
            st.markdown(montant_affiche(pays, montant))
            if st.button("Choisir", key=f"buy_{code}", use_container_width=True):
                st.session_state["achat_en_cours"] = code
                st.rerun()

    if SERVICES:
        st.markdown("#### 🧰 Services à la carte")
        for code, (label, montant) in SERVICES.items():
            g, d = st.columns([3, 1])
            g.markdown(f"**{label}** — {montant_affiche(pays, montant)}")
            if d.button("Payer", key=f"buy_{code}", use_container_width=True):
                st.session_state["achat_en_cours"] = code
                st.rerun()

    # ---- Traitement d'un achat clique -------------------------------------
    code = st.session_state.pop("achat_en_cours", None)
    if code:
        res = lancer_paiement(user, code)
        if not res["ok"]:
            st.error(res["message"])
        elif res["mode"] == "test":
            jours = res["jours"]
            if jours > 0:
                try:
                    import auth
                    nouveau = auth.activer_premium(user["id"], jours)
                    st.session_state.user["premium_jusqu"] = nouveau
                    st.success(f"✅ {res['label']} activé jusqu'au {nouveau} "
                               f"(simulation).")
                except Exception as e:
                    st.error(f"Activation impossible : {e}")
            else:
                info = offre_de_transaction(res["transaction_id"])
                st.success("✅ " + livrer_service(info, user))
            st.balloons()
        else:
            st.link_button(f"💳 Payer {res['montant']} {res['devise']} — "
                           "paiement sécurisé CinetPay", res["url"])
            st.caption("Mobile Money ou carte selon ton pays ; tu reviendras "
                       "ici automatiquement après le paiement.")

    # ---- Historique ---------------------------------------------------------
    h = historique(user["id"])
    if h:
        st.markdown("#### 🧾 Mes paiements")
        for p in h[:8]:
            icone = {"paye": "✅", "echec": "❌"}.get(p["statut"], "⏳")
            st.caption(f"{icone} {p['date'][:16]} · {p['offre']} · "
                       f"{p['montant']} {p['devise']} · {p['statut']}")

    if st.button("← Retour"):
        st.session_state.show_boutique = False
        st.rerun()
    return True
