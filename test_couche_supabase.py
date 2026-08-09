#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_couche_supabase.py — Valide la couche db.py contre la VRAIE base Supabase.
À lancer sur ton Mac, avec DATABASE_URL pointant sur Supabase (Session pooler).

    export DATABASE_URL='postgresql://postgres.xxx:MOTDEPASSE@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
    python3 test_couche_supabase.py
"""
import sys, os
sys.path.insert(0, "app/api")

if not os.environ.get("DATABASE_URL"):
    print("❌ DATABASE_URL manquant. Fais d'abord le export vers Supabase.")
    sys.exit(1)

print("🔌 Connexion à Supabase via la couche db.py...\n")
try:
    import db
except Exception as e:
    print("❌ Impossible de charger db.py :", e); sys.exit(1)

print("Mode PostgreSQL actif ?", db.MODE_PG, "(doit être True)")
if not db.MODE_PG:
    print("❌ La couche est en mode LOCAL. DATABASE_URL n'est pas vu.")
    sys.exit(1)

echecs = 0

# ---- TEST 1 : connexion + lecture simple ----
try:
    con = db.connect()
    con.row_factory = db.Row
    n = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    print(f"✓ TEST 1 — Connexion + lecture : {n} utilisateurs dans Supabase")
except Exception as e:
    print(f"✗ TEST 1 échoué : {e}"); echecs += 1

# ---- TEST 2 : lecture avec placeholder ? (traduit en %s) ----
try:
    con = db.connect(); con.row_factory = db.Row
    row = con.execute("SELECT code FROM config_devises WHERE code=?", ("XOF",)).fetchone()
    val = row["code"] if row else "(aucune)"
    print(f"✓ TEST 2 — Placeholder ?→%s : config_devises code=XOF → {val}")
except Exception as e:
    print(f"✗ TEST 2 échoué : {e}"); echecs += 1

# ---- TEST 3 : lecture accès par NOM de colonne (row_factory) ----
try:
    con = db.connect(); con.row_factory = db.Row
    row = con.execute("SELECT * FROM destinations LIMIT 1").fetchone()
    if row:
        # doit être accessible par nom
        code = row["code"]
        print(f"✓ TEST 3 — Accès par nom de colonne : destinations.code = {code}")
    else:
        print("✓ TEST 3 — table destinations vide (OK)")
except Exception as e:
    print(f"✗ TEST 3 échoué : {e}"); echecs += 1

# ---- TEST 4 : ÉCRITURE réelle — INSERT OR REPLACE (le cas critique) ----
try:
    con = db.connect()
    # écrit une clé de test dans config_params
    con.execute("INSERT OR REPLACE INTO config_params VALUES(?,?)",
                ("__test_couche__", "valeur_A"))
    con.commit()
    # relit
    con2 = db.connect(); con2.row_factory = db.Row
    v1 = con2.execute("SELECT valeur FROM config_params WHERE cle=?",
                      ("__test_couche__",)).fetchone()["valeur"]
    # RÉÉCRIT la même clé (doit REMPLACER, pas ignorer)
    con.execute("INSERT OR REPLACE INTO config_params VALUES(?,?)",
                ("__test_couche__", "valeur_B"))
    con.commit()
    v2 = con2.execute("SELECT valeur FROM config_params WHERE cle=?",
                      ("__test_couche__",)).fetchone()["valeur"]
    if v1 == "valeur_A" and v2 == "valeur_B":
        print(f"✓ TEST 4 — INSERT OR REPLACE : écrit '{v1}' puis remplacé par '{v2}' ✓✓")
    else:
        print(f"✗ TEST 4 — REPLACE n'a pas remplacé : {v1} → {v2}"); echecs += 1
    # nettoyage
    con.execute("DELETE FROM config_params WHERE cle=?", ("__test_couche__",))
    con.commit()
    print("  (clé de test nettoyée)")
except Exception as e:
    print(f"✗ TEST 4 échoué : {e}"); echecs += 1

# ---- TEST 5 : INSERT OR IGNORE (doit ignorer si existe) ----
try:
    con = db.connect(); con.row_factory = db.Row
    # config_pays a une PK 'code'. On tente d'insérer un code qui existe déjà.
    existant = con.execute("SELECT code FROM config_pays LIMIT 1").fetchone()
    if existant:
        code = existant["code"]
        # ne doit PAS lever d'erreur (ON CONFLICT DO NOTHING)
        con.execute("INSERT OR IGNORE INTO config_pays(code,actif) VALUES(?,1)", (code,))
        con.commit()
        print(f"✓ TEST 5 — INSERT OR IGNORE sur code existant '{code}' : ignoré sans erreur")
    else:
        print("✓ TEST 5 — config_pays vide, test sauté")
except Exception as e:
    print(f"✗ TEST 5 échoué : {e}"); echecs += 1

print("\n" + "="*55)
if echecs == 0:
    print("🎉 TOUS LES TESTS RÉUSSIS — la couche fonctionne en RÉEL sur Supabase !")
else:
    print(f"⚠️  {echecs} test(s) échoué(s) — copie ce résultat à Claude.")
