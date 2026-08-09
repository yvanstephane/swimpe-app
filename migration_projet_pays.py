#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migration_projet_pays.py — Yorbity
====================================
1. Localise la base SQLite du projet
2. Affiche le schéma réel (config_pays, config_origines, config_services)
3. Crée la table config_projet_pays si absente
4. Seed des étoiles ⭐ : pose une étoile (destination) quand la fiche
   d'un pays est jugée complète pour un type de projet
5. Seed des origines depuis config_origines (force_actif=1)

Usage :
    cd ~/mobilite-ia && source .venv/bin/activate
    python migration_projet_pays.py            # applique
    python migration_projet_pays.py --dry-run  # montre tout, n'écrit rien

Puis : copier TOUTE la sortie dans Claude.
"""
import sqlite3, os, sys, glob, re, json, datetime

DRY_RUN = "--dry-run" in sys.argv

# ---------------------------------------------------------------- réglages
# Seuils de "complétude" d'une fiche (modifiable)
SEUIL_RESUME = 40    # caractères mini pour qu'un résumé compte
SEUIL_ETAPES = 40    # caractères mini pour que des étapes comptent
SEUIL_GENERIQUE = 80 # si une seule colonne de contenu existe

# Types de projets par défaut si non détectables dans la base.
# >>> ADAPTE cette liste si tes projets canoniques diffèrent (_proj_canon) <<<
PROJETS_DEFAUT = ["etudes", "travail", "tourisme", "affaires", "immigration"]

# Motifs de colonnes "contenu de fiche"
MOTIFS_CONTENU = ("resume", "résumé", "etape", "étape", "fiche", "desc",
                  "contenu", "demarche", "démarche", "process", "info", "detail")
# Motifs de colonnes identifiant le pays
MOTIFS_PAYS = ("code_pays", "code", "iso2", "iso", "pays", "nom_fr", "nom", "country")
# Motifs de colonnes identifiant un type de projet
MOTIFS_PROJET = ("type_projet", "projet", "type", "categorie", "catégorie")

SEP = "=" * 64


# ---------------------------------------------------------------- utilitaires
def find_db():
    env = os.environ.get("YORBITY_DB")
    if env and os.path.exists(env):
        return env
    candidats = []
    for f in glob.glob("*.db") + glob.glob("*.sqlite") + glob.glob("*.sqlite3") \
             + glob.glob("**/*.db", recursive=True):
        if ".venv" in f or "site-packages" in f:
            continue
        if f not in candidats:
            candidats.append(f)
    # priorité aux bases qui contiennent config_pays
    for f in candidats:
        try:
            con = sqlite3.connect(f)
            ok = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='config_pays'"
            ).fetchone()
            con.close()
            if ok:
                return f
        except Exception:
            pass
    if len(candidats) == 1:
        return candidats[0]
    sys.exit("❌ Base SQLite introuvable. Lance le script depuis ~/mobilite-ia "
             "ou indique-la : YORBITY_DB=/chemin/ma_base.db python migration_projet_pays.py")


def colonnes(con, table):
    try:
        return [dict(zip(("cid", "name", "type", "notnull", "dflt", "pk"), r))
                for r in con.execute(f"PRAGMA table_info({table})")]
    except sqlite3.Error:
        return []


def table_existe(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def choisir_colonne(cols, motifs):
    noms = [c["name"] for c in cols]
    bas = {n.lower(): n for n in noms}
    for m in motifs:
        if m in bas:
            return bas[m]
    for m in motifs:
        for n in noms:
            if m in n.lower():
                return n
    return None


def longueur_contenu(val):
    """Longueur 'utile' d'une valeur de fiche (texte brut ou JSON)."""
    if val is None:
        return 0
    s = str(val).strip()
    if not s or s.lower() in ("null", "none", "-", "n/a", "[]", "{}"):
        return 0
    if s[:1] in "[{":
        try:
            data = json.loads(s)
            if isinstance(data, list):
                return sum(len(str(x)) for x in data)
            if isinstance(data, dict):
                return sum(len(str(v)) for v in data.values())
        except Exception:
            pass
    return len(s)


# ---------------------------------------------------------------- main
def main():
    db = find_db()
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row

    print(SEP)
    print(f"MIGRATION config_projet_pays — {datetime.datetime.now():%Y-%m-%d %H:%M}")
    print(f"Base : {os.path.abspath(db)}" + ("   [DRY-RUN : aucune écriture]" if DRY_RUN else ""))
    print(SEP)

    # ---- [A] schémas réels -------------------------------------------------
    print("\n[A] SCHÉMAS RÉELS")
    for t in ("config_pays", "config_origines", "config_services", "config_projet_pays"):
        cols = colonnes(con, t)
        if not cols:
            print(f"  {t:22s} (table absente)")
        else:
            print(f"  {t:22s} " + ", ".join(f"{c['name']}:{c['type'] or '?'}" for c in cols))

    cols_pays = colonnes(con, "config_pays")
    if not cols_pays:
        sys.exit("❌ Table config_pays absente : impossible de seeder.")

    col_id_pays = choisir_colonne(cols_pays, MOTIFS_PAYS)
    if not col_id_pays:
        col_id_pays = cols_pays[0]["name"]
    print(f"\n  → colonne pays retenue dans config_pays : « {col_id_pays} »")

    # échantillon : première ligne de config_pays, valeurs tronquées
    row = con.execute("SELECT * FROM config_pays LIMIT 1").fetchone()
    print("\n[B] ÉCHANTILLON config_pays (1re ligne, valeurs tronquées à 60 car.)")
    for k in row.keys():
        v = str(row[k]) if row[k] is not None else ""
        v = v.replace("\n", "⏎")
        print(f"  {k:24s} = {v[:60]}{'…' if len(v) > 60 else ''}")

    # ---- [C] détection des types de projets --------------------------------
    projets = []
    source_proj = "défaut"
    # 1) une colonne 'projet' dans config_pays ou config_services ?
    for t in ("config_services", "config_pays"):
        cols = colonnes(con, t)
        cp = choisir_colonne(cols, MOTIFS_PROJET)
        if cp:
            try:
                vals = [r[0] for r in con.execute(
                    f"SELECT DISTINCT {cp} FROM {t} WHERE {cp} IS NOT NULL AND TRIM({cp})<>''")]
                if 0 < len(vals) <= 20:
                    projets = sorted(str(v) for v in vals)
                    source_proj = f"{t}.{cp}"
                    break
            except sqlite3.Error:
                pass
    # 2) sinon, colonnes suffixées dans config_pays (ex: resume_etudes)
    if not projets:
        suffixes = set()
        for c in cols_pays:
            n = c["name"].lower()
            for m in MOTIFS_CONTENU:
                if n.startswith(m + "_"):
                    suffixes.add(n.split("_", 1)[1])
        if suffixes:
            projets = sorted(suffixes)
            source_proj = "suffixes de colonnes config_pays"
    if not projets:
        projets = PROJETS_DEFAUT
    print(f"\n[C] TYPES DE PROJETS ({source_proj}) : {', '.join(projets)}")

    # ---- [D] création de la table ------------------------------------------
    print("\n[D] TABLE config_projet_pays")
    if table_existe(con, "config_projet_pays"):
        print("  déjà présente — aucune création.")
    else:
        print("  absente → création." + (" (dry-run : simulée)" if DRY_RUN else ""))
    if not DRY_RUN:
        con.execute("""
            CREATE TABLE IF NOT EXISTS config_projet_pays (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type_projet TEXT NOT NULL,
                code_pays   TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'destination'
                            CHECK(role IN ('origine','destination')),
                etoile      INTEGER NOT NULL DEFAULT 0,   -- ⭐ fiche documentée
                force_actif INTEGER NOT NULL DEFAULT 0,   -- override admin
                maj         TEXT DEFAULT (datetime('now')),
                UNIQUE(type_projet, code_pays, role)
            )""")
        con.execute("""CREATE INDEX IF NOT EXISTS idx_cpp_lookup
                       ON config_projet_pays(type_projet, role, etoile, force_actif)""")

    # ---- [E] seed des étoiles (destinations) -------------------------------
    print("\n[E] SEED DES ÉTOILES (destinations)")
    noms_contenu = [c["name"] for c in cols_pays
                    if any(m in c["name"].lower() for m in MOTIFS_CONTENU)]
    print(f"  colonnes de contenu détectées : {noms_contenu or 'AUCUNE'}")

    # regrouper les colonnes de contenu par projet (suffixe) sinon génériques
    par_projet = {p: [] for p in projets}
    generiques = []
    for n in noms_contenu:
        nl = n.lower()
        cible = None
        for p in projets:
            if nl.endswith("_" + p.lower()) or nl.startswith(p.lower() + "_") or f"_{p.lower()}_" in nl:
                cible = p
                break
        if cible:
            par_projet[cible].append(n)
        else:
            generiques.append(n)

    def fiche_complete(row, cols_ctn):
        if not cols_ctn:
            return False
        lg = {c: longueur_contenu(row[c]) for c in cols_ctn}
        res = [c for c in cols_ctn if "resum" in c.lower() or "résum" in c.lower()]
        eta = [c for c in cols_ctn if "etap" in c.lower() or "étap" in c.lower()]
        if res and eta:
            return max(lg[c] for c in res) >= SEUIL_RESUME and \
                   max(lg[c] for c in eta) >= SEUIL_ETAPES
        return max(lg.values()) >= SEUIL_GENERIQUE

    total_etoiles, detail = 0, {}
    for row in con.execute("SELECT * FROM config_pays"):
        code = str(row[col_id_pays])
        for p in projets:
            cols_ctn = par_projet.get(p) or generiques
            star = 1 if fiche_complete(row, cols_ctn) else 0
            if not DRY_RUN:
                con.execute("""INSERT INTO config_projet_pays(type_projet, code_pays, role, etoile)
                               VALUES(?,?,'destination',?)
                               ON CONFLICT(type_projet, code_pays, role)
                               DO UPDATE SET etoile=excluded.etoile,
                                             maj=datetime('now')""", (p, code, star))
            if star:
                total_etoiles += 1
                detail.setdefault(p, []).append(code)

    for p in projets:
        lst = detail.get(p, [])
        print(f"  {p:14s} : {len(lst):3d} pays étoilés" +
              (f"  → {', '.join(lst[:12])}{'…' if len(lst) > 12 else ''}" if lst else ""))
    print(f"  TOTAL étoiles posées : {total_etoiles}")
    if total_etoiles == 0:
        print("  ⚠️  Aucune étoile : les fiches sont probablement stockées ailleurs")
        print("      (autre table/colonne). Colle ce rapport dans Claude pour ajuster le critère.")

    # ---- [F] seed des origines ---------------------------------------------
    print("\n[F] SEED DES ORIGINES (depuis config_origines)")
    n_org = 0
    if table_existe(con, "config_origines"):
        cols_org = colonnes(con, "config_origines")
        col_org = choisir_colonne(cols_org, MOTIFS_PAYS) or cols_org[0]["name"]
        for r in con.execute(f"SELECT DISTINCT {col_org} FROM config_origines"):
            code = str(r[0])
            for p in projets:
                if not DRY_RUN:
                    con.execute("""INSERT INTO config_projet_pays(type_projet, code_pays, role,
                                                                  etoile, force_actif)
                                   VALUES(?,?,'origine',0,1)
                                   ON CONFLICT(type_projet, code_pays, role)
                                   DO UPDATE SET force_actif=1, maj=datetime('now')""", (p, code))
                n_org += 1
        print(f"  colonne pays : « {col_org} » — {n_org} lignes origine insérées/mises à jour.")
    else:
        print("  table config_origines absente — rien à faire.")

    if not DRY_RUN:
        con.commit()

    # ---- [G] état final ------------------------------------------------------
    print("\n[G] ÉTAT FINAL config_projet_pays")
    if table_existe(con, "config_projet_pays"):
        for r in con.execute("""SELECT type_projet, role,
                                       COUNT(*) n,
                                       SUM(etoile) etoiles,
                                       SUM(force_actif) forces
                                FROM config_projet_pays
                                GROUP BY type_projet, role ORDER BY 1,2"""):
            print(f"  {r['type_projet']:14s} {r['role']:12s} lignes={r['n']:4d} "
                  f"⭐={r['etoiles'] or 0:3d} forcés={r['forces'] or 0:3d}")
    con.close()
    print("\n" + SEP)
    print("FIN — copie TOUTE cette sortie dans Claude")
    print(SEP)


if __name__ == "__main__":
    main()
