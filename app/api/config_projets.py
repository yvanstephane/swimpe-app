# =============================================================================
# config_projets.py — Contrôle par TYPE DE PROJET (Formation / Bourse / Stage)
# Pour chaque (projet, rôle[origine|destination], pays) :
#   - etoile : info vérifiée (auto si fiche détaillée, forçable par admin)
#   - actif  : visible côté visiteur
# Règle : un pays est visible s'il a l'étoile OU s'il est activé manuellement.
# =============================================================================
import sqlite3

DB = "data/mobilite.db"

# Les 3 types de projet (clés canoniques, indépendantes de la langue)
PROJETS = ["Formation (admission)", "Bourse", "Stage / Emploi étudiant", "Métier spécialisé", "Sport", "Art", "Volontariat"]

def _init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS config_projet_pays(
        projet TEXT, role TEXT, pays TEXT,
        etoile INT DEFAULT 0, actif INT DEFAULT 0,
        force_admin INT DEFAULT 0,
        PRIMARY KEY(projet, role, pays))""")
    con.commit(); con.close()

def seed_etoiles(projet, role, pays_verifies):
    """Pose l'étoile (auto) sur les pays dont l'info est vérifiée pour ce projet,
    sauf si l'admin a déjà forcé une valeur manuelle (force_admin=1)."""
    _init()
    con = sqlite3.connect(DB)
    for p in pays_verifies:
        row = con.execute("SELECT force_admin FROM config_projet_pays "
                          "WHERE projet=? AND role=? AND pays=?",
                          (projet, role, p)).fetchone()
        if row is None:
            # nouvelle entrée : étoile auto + actif (visible par défaut car vérifié)
            con.execute("INSERT INTO config_projet_pays(projet,role,pays,etoile,actif,force_admin) "
                        "VALUES(?,?,?,1,1,0)", (projet, role, p))
        elif row[0] == 0:
            con.execute("UPDATE config_projet_pays SET etoile=1 WHERE projet=? AND role=? AND pays=?",
                        (projet, role, p))
    con.commit(); con.close()

def etat(projet, role):
    """dict {pays: (etoile, actif)} pour ce projet+rôle."""
    _init()
    con = sqlite3.connect(DB)
    rows = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT pays, etoile, actif FROM config_projet_pays WHERE projet=? AND role=?",
        (projet, role))}
    con.close()
    return rows

def pays_visibles(projet, role):
    """Visible cote visiteur = pays ACTIF. L'etoile est un badge admin :
    on peut activer un pays sans etoile ou masquer un pays etoile."""
    return [p for p, (et, ac) in etat(projet, role).items() if ac]

def definir(projet, role, pays, etoile=None, actif=None):
    """Modifie l'étoile et/ou l'activation d'un pays. Marque force_admin."""
    _init()
    con = sqlite3.connect(DB)
    row = con.execute("SELECT etoile, actif FROM config_projet_pays "
                      "WHERE projet=? AND role=? AND pays=?",
                      (projet, role, pays)).fetchone()
    et, ac = (row if row else (0, 0))
    if etoile is not None: et = 1 if etoile else 0
    if actif is not None:  ac = 1 if actif else 0
    con.execute("INSERT OR REPLACE INTO config_projet_pays(projet,role,pays,etoile,actif,force_admin) "
                "VALUES(?,?,?,?,?,1)", (projet, role, pays, et, ac))
    con.commit(); con.close()
