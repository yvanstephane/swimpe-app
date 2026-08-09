# =============================================================================
# services_cfg.py — Services proposés PAR destination, configurables en admin
# Stockés en base (table config_services). Au premier passage sur une
# destination, les valeurs par défaut du code sont copiées en base ;
# ensuite, seul l'admin décide (cases à cocher).
# =============================================================================
import sqlite3

DB = "data/mobilite.db"

def _init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS config_services(
        destination TEXT, service TEXT, actif INT,
        PRIMARY KEY(destination, service))""")
    con.commit(); con.close()

def effectifs(destination, defauts, catalogue):
    """Liste des codes services actifs pour cette destination.
    - defauts   : liste par défaut définie dans le code (D[c]['services'])
    - catalogue : tous les codes possibles (ordre d'affichage = ordre du catalogue)
    Au premier appel pour une destination, initialise la base avec les défauts."""
    _init()
    con = sqlite3.connect(DB)
    rows = dict(con.execute(
        "SELECT service, actif FROM config_services WHERE destination=?",
        (destination,)).fetchall())
    if not rows:
        for s in catalogue:
            con.execute("INSERT OR IGNORE INTO config_services VALUES(?,?,?)",
                        (destination, s, 1 if s in defauts else 0))
        con.commit(); con.close()
        return [s for s in catalogue if s in defauts]
    con.close()
    return [s for s in catalogue if rows.get(s, 1 if s in defauts else 0) == 1]

def definir(destination, service, actif):
    _init()
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO config_services VALUES(?,?,?)",
                (destination, service, 1 if actif else 0))
    con.commit(); con.close()


# =============================================================================
# Origines activables/désactivables (indépendamment des destinations)
# Par défaut : toutes actives. L'admin peut en masquer.
# =============================================================================
def _init_origines():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS config_origines(nom TEXT PRIMARY KEY, actif INT)")
    con.commit(); con.close()

def origines_desactivees():
    _init_origines()
    con = sqlite3.connect(DB)
    rows = {r[0] for r in con.execute("SELECT nom FROM config_origines WHERE actif=0")}
    con.close()
    return rows

def definir_origine(nom, actif):
    _init_origines()
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO config_origines VALUES(?,?)", (nom, 1 if actif else 0))
    con.commit(); con.close()


# =============================================================================
# Tarifs des services — modifiables par l'admin (défauts = ceux du code)
# =============================================================================
def _init_tarifs():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS config_tarifs(service TEXT PRIMARY KEY, prix INT)")
    con.commit(); con.close()

def tarifs_tous(defauts):
    """dict {code: prix effectif} — prix admin si défini, sinon défaut du code."""
    _init_tarifs()
    con = sqlite3.connect(DB)
    rows = dict(con.execute("SELECT service, prix FROM config_tarifs"))
    con.close()
    return {k: rows.get(k, v) for k, v in defauts.items()}

def definir_tarif(service, prix):
    _init_tarifs()
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO config_tarifs VALUES(?,?)", (service, int(prix)))
    con.commit(); con.close()
