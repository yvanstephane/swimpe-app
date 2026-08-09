# =============================================================================
# securite.py — Monitoring de sécurité défensif Yorbity (back-end)
# - Journalise les événements de sécurité dans SQLite (table security_events)
# - Règles de détection simples (ex : rafale d'échecs de connexion)
# - Générateur de données factices pour la démo SOC
# AUCUN code offensif : uniquement journalisation, détection, visualisation.
# =============================================================================
import sqlite3, datetime, random, hashlib

DB = "data/mobilite.db"

SEVERITES = ("info", "faible", "moyen", "eleve", "critique")

TYPES_EVENEMENTS = {
    "login_ok":        ("Connexion réussie", "info"),
    "login_echec":     ("Échec de connexion", "faible"),
    "login_rafale":    ("Rafale d'échecs de connexion (possible force brute)", "eleve"),
    "admin_acces":     ("Accès au panneau admin", "moyen"),
    "admin_echec":     ("Mot de passe admin incorrect", "moyen"),
    "inscription":     ("Nouveau compte créé", "info"),
    "paiement_ok":     ("Paiement validé", "info"),
    "paiement_echec":  ("Paiement échoué", "faible"),
    "requete_anormale":("Entrée utilisateur suspecte détectée", "moyen"),
    "export_donnees":  ("Export de données par un admin", "moyen"),
}

# ----------------------------------------------------------------------------
# Initialisation
# ----------------------------------------------------------------------------
def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS security_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horodatage TEXT,
        type TEXT,
        severite TEXT,
        description TEXT,
        acteur TEXT,          -- email masqué ou 'anonyme'
        ip_hash TEXT,         -- jamais l'IP en clair : hash (protection vie privée)
        detail TEXT
    )""")
    con.commit(); con.close()

def _masque_email(email):
    """j***@d***.com — on journalise sans exposer l'identité complète."""
    if not email or "@" not in email:
        return "anonyme"
    nom, dom = email.split("@", 1)
    return f"{nom[:1]}***@{dom[:1]}***{dom[dom.rfind('.'):]}"

def _hash_ip(ip):
    """L'IP n'est JAMAIS stockée en clair (RGPD) : hash tronqué, suffisant
    pour corréler des événements sans identifier la personne."""
    if not ip:
        return "-"
    return hashlib.sha256(ip.encode()).hexdigest()[:12]

# ----------------------------------------------------------------------------
# Journalisation (à appeler depuis auth.py / ui.py)
# ----------------------------------------------------------------------------
def log(type_evt, acteur_email="", ip="", detail=""):
    init_db()
    libelle, sev = TYPES_EVENEMENTS.get(type_evt, (type_evt, "info"))
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO security_events(horodatage,type,severite,description,acteur,ip_hash,detail) "
                "VALUES(?,?,?,?,?,?,?)",
                (datetime.datetime.now().isoformat(timespec="seconds"),
                 type_evt, sev, libelle, _masque_email(acteur_email),
                 _hash_ip(ip), detail[:500]))
    con.commit()

    # --- Règle de détection : rafale d'échecs de connexion -------------------
    if type_evt == "login_echec":
        dix_min = (datetime.datetime.now() - datetime.timedelta(minutes=10)).isoformat()
        n = con.execute(
            "SELECT COUNT(*) FROM security_events WHERE type='login_echec' "
            "AND acteur=? AND horodatage>?",
            (_masque_email(acteur_email), dix_min)).fetchone()[0]
        if n >= 5:
            con.execute("INSERT INTO security_events(horodatage,type,severite,description,acteur,ip_hash,detail) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (datetime.datetime.now().isoformat(timespec="seconds"),
                         "login_rafale", "eleve",
                         TYPES_EVENEMENTS["login_rafale"][0],
                         _masque_email(acteur_email), _hash_ip(ip),
                         f"{n} échecs en 10 minutes"))
            con.commit()
    con.close()

# ----------------------------------------------------------------------------
# Lecture pour le tableau de bord
# ----------------------------------------------------------------------------
def evenements(limite=500):
    init_db()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT ?",
                       (limite,)).fetchall()
    con.close()
    return [dict(r) for r in rows]

def stats():
    init_db()
    con = sqlite3.connect(DB)
    total = con.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
    par_sev = dict(con.execute(
        "SELECT severite, COUNT(*) FROM security_events GROUP BY severite").fetchall())
    aujourdhui = con.execute(
        "SELECT COUNT(*) FROM security_events WHERE horodatage LIKE ?",
        (datetime.date.today().isoformat() + "%",)).fetchone()[0]
    critiques = con.execute(
        "SELECT COUNT(*) FROM security_events WHERE severite IN ('eleve','critique')").fetchone()[0]
    con.close()
    return {"total": total, "par_severite": par_sev,
            "aujourdhui": aujourdhui, "critiques": critiques}

# ----------------------------------------------------------------------------
# Données factices pour la démo SOC
# ----------------------------------------------------------------------------
def generer_demo(n=60):
    """Génère n événements factices répartis sur les 7 derniers jours."""
    init_db()
    random.seed(42)
    emails = ["marie@exemple.com", "jean@test.org", "fatou@demo.ga",
              "chen@sample.cn", "admin@yorbity.com", "carlos@mail.br"]
    ips = ["203.0.113." + str(i) for i in range(1, 20)]  # plage IP de documentation
    types = list(TYPES_EVENEMENTS.keys())
    poids  = [30, 20, 2, 5, 3, 15, 10, 5, 6, 4]  # fréquences réalistes
    con = sqlite3.connect(DB)
    maintenant = datetime.datetime.now()
    for _ in range(n):
        t = random.choices(types, weights=poids)[0]
        libelle, sev = TYPES_EVENEMENTS[t]
        quand = maintenant - datetime.timedelta(
            days=random.uniform(0, 7))
        con.execute("INSERT INTO security_events(horodatage,type,severite,description,acteur,ip_hash,detail) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (quand.isoformat(timespec="seconds"), t, sev, libelle,
                     _masque_email(random.choice(emails)),
                     _hash_ip(random.choice(ips)),
                     "événement de démonstration"))
    con.commit(); con.close()
    return n

if __name__ == "__main__":
    n = generer_demo()
    s = stats()
    print(f"✓ {n} événements de démo générés.")
    print(f"  Total en base : {s['total']} · Alertes élevées/critiques : {s['critiques']}")
    print("  Génère le dashboard : python scripts/genere_dashboard_securite.py")
