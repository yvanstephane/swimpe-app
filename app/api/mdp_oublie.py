# =============================================================================
# mdp_oublie.py — « Mot de passe oublié » en libre-service (sécurisé)
# Code à 6 chiffres HACHÉ en base, valable 15 min, 3 essais max, usage unique.
# Envoi par e-mail (SMTP Gmail via YORBITY_SMTP_USER / YORBITY_SMTP_PASS) et,
# si configuré, par WhatsApp (Twilio : TWILIO_SID / TWILIO_TOKEN /
# TWILIO_WHATSAPP_FROM). Réponse générique : on ne révèle jamais si un e-mail
# possède un compte (anti-énumération).
# =============================================================================
import streamlit as st
import sqlite3, secrets, datetime, os, smtplib, ssl, base64
import urllib.request, urllib.parse
from email.mime.text import MIMEText
import auth

DB = "data/mobilite.db"
VALIDITE_MIN = 15
MAX_ESSAIS = 3


def _env(cle, defaut=""):
    v = os.environ.get(cle)
    if v:
        return v
    for chemin in (".env", "app/.env", "app/api/.env"):
        if os.path.exists(chemin):
            for l in open(chemin, encoding="utf-8", errors="ignore"):
                l = l.strip()
                if l.startswith(cle + "="):
                    return l.split("=", 1)[1].strip().strip('"').strip("'")
    return defaut


def whatsapp_dispo():
    return bool(_env("TWILIO_SID") and _env("TWILIO_TOKEN") and _env("TWILIO_WHATSAPP_FROM"))


def _init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS reset_codes(
        user_id INTEGER PRIMARY KEY, code_hash TEXT, code_salt TEXT,
        expire TEXT, essais INT DEFAULT 0)""")
    con.commit(); con.close()


def _envoyer_email(dest, code):
    user = _env("YORBITY_SMTP_USER"); pwd = _env("YORBITY_SMTP_PASS")
    if not (user and pwd) or pwd == "A_REMPLACER":
        return False, ("Envoi d'e-mail non configuré. Mettez YORBITY_SMTP_PASS "
                       "(mot de passe d'application Gmail) dans le fichier .env.")
    try:
        msg = MIMEText(f"Votre code de récupération Swimpe : {code}\n"
                       f"Valable {VALIDITE_MIN} minutes ({MAX_ESSAIS} essais max).\n"
                       "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.",
                       _charset="utf-8")
        msg["Subject"] = "Swimpe — code de récupération"
        msg["From"] = user; msg["To"] = dest
        hote = _env("YORBITY_SMTP_HOST", "smtp.gmail.com")
        port = int(_env("YORBITY_SMTP_PORT", "465"))
        with smtplib.SMTP_SSL(hote, port, context=ssl.create_default_context(),
                              timeout=15) as s:
            s.login(user, pwd)
            s.sendmail(user, [dest], msg.as_string())
        return True, None
    except Exception as e:
        return False, f"Échec d'envoi e-mail : {e}"


def _envoyer_whatsapp(tel, code):
    sid = _env("TWILIO_SID"); tok = _env("TWILIO_TOKEN"); dep = _env("TWILIO_WHATSAPP_FROM")
    if not (sid and tok and dep):
        return False, "WhatsApp non configuré."
    if not tel:
        return False, "Aucun numéro de téléphone enregistré sur ce compte."
    tel = tel.strip().replace(" ", "")
    if not tel.startswith("+"):
        tel = "+" + tel
    try:
        data = urllib.parse.urlencode({
            "From": f"whatsapp:{dep}", "To": f"whatsapp:{tel}",
            "Body": f"Swimpe — code de récupération : {code} "
                    f"(valable {VALIDITE_MIN} min)"}).encode()
        req = urllib.request.Request(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data=data)
        req.add_header("Authorization",
                       "Basic " + base64.b64encode(f"{sid}:{tok}".encode()).decode())
        urllib.request.urlopen(req, timeout=15).read()
        return True, None
    except Exception as e:
        return False, f"Échec WhatsApp : {e}"


def demander_code(email, canal="email"):
    """Génère et envoie un code. Retourne (ok, erreur_ou_None).
    Si l'e-mail n'a pas de compte : ok=True quand même (anti-énumération)."""
    email = (email or "").strip().lower()
    _init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    row = con.execute("SELECT id, email, telephone FROM users WHERE email=?",
                      (email,)).fetchone()
    con.close()
    if not row:
        return True, None
    code = f"{secrets.randbelow(10**6):06d}"
    salt = secrets.token_hex(8)
    exp = (datetime.datetime.now()
           + datetime.timedelta(minutes=VALIDITE_MIN)).isoformat(timespec="seconds")
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO reset_codes VALUES(?,?,?,?,0)",
                (row["id"], auth._hash(code, salt), salt, exp))
    con.commit(); con.close()
    if canal == "whatsapp":
        ok, err = _envoyer_whatsapp(row["telephone"], code)
    else:
        ok, err = _envoyer_email(row["email"], code)
    try:
        import securite
        securite.log("mdp_code_envoye", email, detail=f"canal={canal}, ok={ok}")
    except Exception:
        pass
    return ok, err


def verifier_code(email, code):
    """Retourne (True, user_id) ou (False, message). Usage unique, 3 essais."""
    email = (email or "").strip().lower()
    _init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        u = con.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not u:
            return False, "Code invalide."
        r = con.execute("SELECT * FROM reset_codes WHERE user_id=?", (u["id"],)).fetchone()
        if not r:
            return False, "Code invalide."
        if r["essais"] >= MAX_ESSAIS:
            return False, "Trop d'essais. Redemandez un nouveau code."
        try:
            if datetime.datetime.fromisoformat(r["expire"]) < datetime.datetime.now():
                return False, "Code expiré. Redemandez un nouveau code."
        except Exception:
            pass
        if auth._hash((code or "").strip(), r["code_salt"]) != r["code_hash"]:
            con.execute("UPDATE reset_codes SET essais=essais+1 WHERE user_id=?", (u["id"],))
            con.commit()
            return False, "Code invalide."
        con.execute("DELETE FROM reset_codes WHERE user_id=?", (u["id"],))
        con.commit()
        return True, u["id"]
    finally:
        con.close()


def ecran():
    """Écran « Mot de passe oublié ». True si affiché (bloque la page)."""
    if not st.session_state.get("show_mdp_oublie"):
        return False
    st.markdown("## 🔑 Mot de passe oublié")
    etape = st.session_state.get("mdpo_etape", 1)

    if etape == 1:
        with st.form("mdpo_email"):
            email = st.text_input("Votre adresse e-mail")
            canaux = ["E-mail"] + (["WhatsApp"] if whatsapp_dispo() else [])
            canal = st.radio("Recevoir le code par", canaux, horizontal=True)
            c1, c2 = st.columns(2)
            ok = c1.form_submit_button("Envoyer le code", type="primary",
                                       use_container_width=True)
            annul = c2.form_submit_button("← Retour", use_container_width=True)
        if annul:
            st.session_state.show_mdp_oublie = False
            st.session_state.show_auth = True
            st.rerun()
        if ok:
            envoye, err = demander_code(email,
                                        "whatsapp" if canal == "WhatsApp" else "email")
            if envoye:
                st.session_state["_mdpo_email"] = (email or "").strip().lower()
                st.session_state.mdpo_etape = 2
                st.rerun()
            else:
                st.error(err)

    elif etape == 2:
        st.info(f"Si un compte existe avec cette adresse, un code à 6 chiffres "
                f"a été envoyé (valable {VALIDITE_MIN} min, {MAX_ESSAIS} essais).")
        with st.form("mdpo_code"):
            code = st.text_input("Code reçu")
            n1 = st.text_input("Nouveau mot de passe", type="password")
            n2 = st.text_input("Confirmez le nouveau mot de passe", type="password")
            c1, c2 = st.columns(2)
            ok = c1.form_submit_button("Valider", type="primary", use_container_width=True)
            annul = c2.form_submit_button("← Retour", use_container_width=True)
        if annul:
            st.session_state.mdpo_etape = 1
            st.rerun()
        if ok:
            if n1 != n2:
                st.error("Les deux mots de passe ne correspondent pas.")
            else:
                v, res = verifier_code(st.session_state.get("_mdpo_email", ""), code)
                if not v:
                    st.error(res)
                else:
                    okc, msg = auth.definir_nouveau_mdp(res, n1)
                    if okc:
                        st.session_state.mdpo_etape = 3
                        st.rerun()
                    else:
                        st.error(msg)

    else:
        st.success("✅ Mot de passe changé. Vous pouvez vous connecter.")
        if st.button("Se connecter", type="primary"):
            for k in ("show_mdp_oublie", "mdpo_etape", "_mdpo_email"):
                st.session_state.pop(k, None)
            st.session_state.show_auth = True
            st.rerun()
    return True
