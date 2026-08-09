# =============================================================================
# auth.py — Comptes utilisateurs Yorbity (inscription, connexion, sécurité)
# Mots de passe chiffrés (PBKDF2-SHA256, jamais stockés en clair).
# Rôles : "etudiant" (par défaut) ou "admin".
# =============================================================================
import sqlite3, hashlib, os, secrets, datetime, re

DB = "data/mobilite.db"

# ----------------------------------------------------------------------------
# Schéma de la table utilisateurs
# ----------------------------------------------------------------------------
def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nom TEXT,
        pays_origine TEXT,
        telephone TEXT,
        pwd_hash TEXT NOT NULL,
        pwd_salt TEXT NOT NULL,
        role TEXT DEFAULT 'etudiant',
        premium_jusqu TEXT,
        cree_le TEXT
    )""")
    con.commit()
    con.close()

# ----------------------------------------------------------------------------
# Sécurité des mots de passe
# ----------------------------------------------------------------------------
def _hash(pwd: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256, 200 000 itérations."""
    return hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt.encode(), 200_000).hex()

def _valide_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def _valide_pwd(pwd: str):
    """Retourne None si OK, sinon un message d'erreur."""
    if len(pwd) < 8:
        return "Le mot de passe doit faire au moins 8 caractères."
    if not any(c.isdigit() for c in pwd):
        return "Le mot de passe doit contenir au moins un chiffre."
    return None

# ----------------------------------------------------------------------------
# Inscription
# ----------------------------------------------------------------------------
def inscrire(email, nom, pwd, pays_origine="", telephone=""):
    """Retourne (True, user_id) ou (False, message_erreur)."""
    email = (email or "").strip().lower()
    if not _valide_email(email):
        return False, "Adresse e-mail invalide."
    err = _valide_pwd(pwd)
    if err:
        return False, err
    con = sqlite3.connect(DB)
    try:
        existe = con.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone()
        if existe:
            return False, "Un compte existe déjà avec cet e-mail. Connecte-toi."
        salt = secrets.token_hex(16)
        h = _hash(pwd, salt)
        con.execute(
            "INSERT INTO users(email,nom,pays_origine,telephone,pwd_hash,pwd_salt,role,cree_le) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (email, " ".join((nom or "").split()), pays_origine, telephone.strip(), h, salt, "etudiant",
             datetime.date.today().isoformat()))
        con.commit()
        uid = con.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
        return True, uid
    finally:
        con.close()

# ----------------------------------------------------------------------------
# Connexion
# ----------------------------------------------------------------------------
def connecter(email, pwd):
    """Retourne (True, dict_user) ou (False, message_erreur)."""
    email = (email or "").strip().lower()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            return False, "Aucun compte avec cet e-mail."
        if _hash(pwd, row["pwd_salt"]) != row["pwd_hash"]:
            try:
                import securite; securite.log("login_echec", email)
            except Exception:
                pass
            return False, "Mot de passe incorrect."
        r = dict(row)
        if r.get("pwd_temp"):
            exp = r.get("pwd_temp_expire") or ""
            try:
                if datetime.datetime.fromisoformat(exp) < datetime.datetime.now():
                    return False, ("Mot de passe temporaire expiré. "
                                   "Demande une nouvelle réinitialisation à l'admin.")
            except Exception:
                pass
        return True, {
            "id": row["id"], "email": row["email"], "nom": row["nom"],
            "role": row["role"], "pays_origine": row["pays_origine"],
            "telephone": row["telephone"], "premium_jusqu": row["premium_jusqu"],
            "pwd_temp": bool(r.get("pwd_temp")),
        }
    finally:
        con.close()

# ----------------------------------------------------------------------------
# Réinitialisation sécurisée des comptes (admin) + changement de mot de passe
# ----------------------------------------------------------------------------
def _init_reset():
    """Ajoute les colonnes du mot de passe temporaire si absentes (idempotent)."""
    con = sqlite3.connect(DB)
    for ddl in ("ALTER TABLE users ADD COLUMN pwd_temp INT DEFAULT 0",
                "ALTER TABLE users ADD COLUMN pwd_temp_expire TEXT"):
        try:
            con.execute(ddl)
        except sqlite3.OperationalError:
            pass
    con.commit(); con.close()

def lister_utilisateurs():
    """Liste minimale pour l'écran admin (jamais de hash ni de sel)."""
    _init_reset()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT id, email, nom, role, premium_jusqu, cree_le, pwd_temp "
                       "FROM users ORDER BY id").fetchall()
    con.close()
    return [dict(r) for r in rows]

def reinitialiser_mdp(user_id):
    """(Admin) Remplace le mot de passe par un TEMPORAIRE aléatoire, valable 24 h,
    à changer obligatoirement à la première connexion. Retourne (ok, temp_ou_msg)."""
    _init_reset()
    temp = secrets.token_urlsafe(9)
    salt = secrets.token_hex(16)
    exp = (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat(timespec="seconds")
    con = sqlite3.connect(DB)
    try:
        row = con.execute("SELECT email FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return False, "Utilisateur introuvable."
        con.execute("UPDATE users SET pwd_hash=?, pwd_salt=?, pwd_temp=1, pwd_temp_expire=? "
                    "WHERE id=?", (_hash(temp, salt), salt, exp, user_id))
        con.commit()
    finally:
        con.close()
    try:
        import securite
        securite.log("mdp_reinitialise", row[0], detail=f"reset admin, expire {exp}")
    except Exception:
        pass
    return True, temp

def changer_mdp(user_id, ancien, nouveau):
    """Change le mot de passe (vérifie l'ancien, valide le nouveau, retire le
    drapeau temporaire). Retourne (ok, message)."""
    _init_reset()
    err = _valide_pwd(nouveau)
    if err:
        return False, err
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return False, "Utilisateur introuvable."
        if _hash(ancien, row["pwd_salt"]) != row["pwd_hash"]:
            return False, "Ancien mot de passe incorrect."
        salt = secrets.token_hex(16)
        con.execute("UPDATE users SET pwd_hash=?, pwd_salt=?, pwd_temp=0, pwd_temp_expire=NULL "
                    "WHERE id=?", (_hash(nouveau, salt), salt, user_id))
        con.commit()
    finally:
        con.close()
    try:
        import securite
        securite.log("mdp_change", row["email"], detail="changement par l'utilisateur")
    except Exception:
        pass
    return True, "Mot de passe changé."

def definir_nouveau_mdp(user_id, nouveau):
    """Définit un nouveau mot de passe après vérification d'un code de
    récupération (mdp_oublie). Retourne (ok, message)."""
    _init_reset()
    err = _valide_pwd(nouveau)
    if err:
        return False, err
    salt = secrets.token_hex(16)
    con = sqlite3.connect(DB)
    row = con.execute("SELECT email FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        con.close(); return False, "Utilisateur introuvable."
    con.execute("UPDATE users SET pwd_hash=?, pwd_salt=?, pwd_temp=0, pwd_temp_expire=NULL "
                "WHERE id=?", (_hash(nouveau, salt), salt, user_id))
    con.commit(); con.close()
    try:
        import securite
        securite.log("mdp_change", row[0], detail="via code de récupération")
    except Exception:
        pass
    return True, "Mot de passe changé. Connecte-toi."

# ----------------------------------------------------------------------------
# Statut Premium
# ----------------------------------------------------------------------------
def est_premium(user: dict) -> bool:
    d = user.get("premium_jusqu")
    if not d:
        return False
    try:
        return datetime.date.fromisoformat(d) >= datetime.date.today()
    except Exception:
        return False

def activer_premium(user_id, jours=30):
    """Prolonge l'abonnement Premium de N jours (appelé après paiement validé)."""
    con = sqlite3.connect(DB)
    row = con.execute("SELECT premium_jusqu FROM users WHERE id=?", (user_id,)).fetchone()
    base = datetime.date.today()
    if row and row[0]:
        try:
            actuel = datetime.date.fromisoformat(row[0])
            if actuel > base:
                base = actuel
        except Exception:
            pass
    nouveau = (base + datetime.timedelta(days=jours)).isoformat()
    con.execute("UPDATE users SET premium_jusqu=? WHERE id=?", (nouveau, user_id))
    con.commit()
    con.close()
    return nouveau

# ----------------------------------------------------------------------------
# Créer le premier admin (à lancer une fois depuis le terminal)
# ----------------------------------------------------------------------------
def creer_admin(email, nom, pwd):
    init_db()
    ok, res = inscrire(email, nom, pwd)
    if ok:
        con = sqlite3.connect(DB)
        con.execute("UPDATE users SET role='admin' WHERE id=?", (res,))
        con.commit()
        con.close()
        return f"✅ Admin créé : {email}"
    return f"❌ {res}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4:
        print(creer_admin(sys.argv[1], sys.argv[2], sys.argv[3]))
    else:
        print("Usage : python app/api/auth.py <email> <nom> <motdepasse>")
