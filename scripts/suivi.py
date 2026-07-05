#!/usr/bin/env python3
# =============================================================================
# suivi.py — Tableau de bord TERMINAL du projet (commande : make suivi)
# Affiche : avancement des tâches du plan, état de la matrice corridors,
# fraîcheur des données, opportunités en base, prochaines actions.
# =============================================================================
import sqlite3, re, os, datetime

PLAN = "docs/PLAN_MOBILITE_IA.md"
ANNEXES = ["docs/ANNEXE_CORRIDORS.md", "docs/ANNEXE_B_MATRICE_MONDIALE.md"]
DB = "data/mobilite.db"
TODAY = datetime.date.today()

def barre(pct, larg=30):
    n = int(pct * larg / 100)
    return "█" * n + "░" * (larg - n)

def taches():
    done, todo, prochaines = 0, 0, []
    for f in [PLAN] + ANNEXES:
        if not os.path.exists(f):
            continue
        for ligne in open(f, encoding="utf-8"):
            if re.search(r"\[x\] T-\d+", ligne):
                done += 1
            elif re.search(r"\[ \] T-\d+", ligne):
                todo += 1
                if len(prochaines) < 3:
                    prochaines.append(ligne.strip().lstrip("- "))
    return done, todo, prochaines

def main():
    print("=" * 62)
    print(f"  MOBILITÉ-IA — SUIVI DU PROJET        {TODAY}")
    print("=" * 62)

    # 1. Avancement des tâches
    done, todo, prochaines = taches()
    total = done + todo
    pct = round(100 * done / total) if total else 0
    print(f"\n📋 TÂCHES : {done}/{total} terminées  [{barre(pct)}] {pct}%")
    if prochaines:
        print("   Prochaines actions :")
        for p in prochaines:
            print(f"   → {p[:70]}")

    # 2. Base de données
    if not os.path.exists(DB):
        print("\n⚠️  data/mobilite.db absente → lance : python scripts/gen_matrice.py")
        return
    con = sqlite3.connect(DB)
    cur = con.cursor()

    def compte(sql, defaut=0):
        try:
            return cur.execute(sql).fetchone()[0]
        except sqlite3.OperationalError:
            return defaut

    # 3. Matrice corridors
    n_cor = compte("SELECT COUNT(*) FROM corridors")
    n_ver = compte("SELECT COUNT(*) FROM corridors WHERE statut='verifie'")
    n_dest = compte("SELECT COUNT(*) FROM destinations WHERE statut='verifie'")
    print(f"\n🌍 MATRICE : {n_cor} corridors | {n_ver} vérifiés | "
          f"{n_dest}/30 fiches destination vérifiées")
    top = cur.execute(
        "SELECT origine, destination, score FROM corridors "
        "ORDER BY score DESC LIMIT 5").fetchall()
    if top and top[0][2] > 0:
        print("   Top corridors : " + ", ".join(f"{o}→{d}({s})" for o, d, s in top))

    # 4. Opportunités (formations, bourses, emplois, stages)
    n_opp = compte("SELECT COUNT(*) FROM opportunites")
    if n_opp:
        print(f"\n🎯 OPPORTUNITÉS EN BASE : {n_opp}")
        for typ, n in cur.execute(
                "SELECT type, COUNT(*) FROM opportunites GROUP BY type"):
            print(f"   • {typ:<10} : {n}")
        # Fraîcheur
        perimees = compte(
            f"SELECT COUNT(*) FROM opportunites "
            f"WHERE julianday('{TODAY}') - julianday(maj) > 90")
        if perimees:
            print(f"   ⚠️  {perimees} fiches > 90 jours → make collect")
    else:
        print("\n🎯 OPPORTUNITÉS : aucune — lance : make collect (ou seed_demo)")

    # 5. Rappel des commandes
    print("\n" + "-" * 62)
    print("  COMMANDES : make suivi | make plan | make agent | make collect")
    print("              make dashboard | make backup")
    print("-" * 62)
    con.close()

if __name__ == "__main__":
    main()
