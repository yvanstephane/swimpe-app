#!/usr/bin/env python3
"""
patch_branchement_moteur_plans_v1.py
Branche moteur_plans dans ui.py : 1 import + 1 bloc admin.
Idempotent · .bak horodaté · ast.parse · restauration si casse.
Ancres exactes extraites de ui.py (lignes 35 et 1034).
Usage : python3 patch_branchement_moteur_plans_v1.py
"""
import ast, shutil, sys
from datetime import datetime
from pathlib import Path

CIBLE = Path.home() / "mobilite-ia/app/api/ui.py"

ANCRE_IMPORT = "import espace, auth, dossiers, services_cfg, config_projets, admin_projets, admin_comptes, mdp_oublie, opportunites_ui, offres_cfg, devises_cfg, eligibilite, offres_sync, recherche_poste"
NOUVEL_IMPORT = ANCRE_IMPORT + ", moteur_plans"

ANCRE_ADMIN = """if espace.est_admin() and offres_sync.ecran():
    st.stop()"""
NOUVEAU_ADMIN = ANCRE_ADMIN + """
if espace.est_admin() and moteur_plans.ecran(ORIGINES):
    st.stop()"""

def main():
    if not CIBLE.exists():
        sys.exit(f"❌ Introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")

    if "moteur_plans.ecran" in src:
        print("ℹ️  Branchement déjà présent — rien à faire.")
        sys.exit(0)

    if ANCRE_IMPORT not in src:
        sys.exit("❌ Ancre d'import introuvable — ui.py modifié ? Abandon.")
    if ANCRE_ADMIN not in src:
        sys.exit("❌ Ancre du bloc admin (offres_sync) introuvable — abandon.")
    # Sécurité : les deux ancres doivent être uniques
    if src.count(ANCRE_IMPORT) != 1 or src.count(ANCRE_ADMIN) != 1:
        sys.exit("❌ Ancre non unique — abandon par prudence.")

    bak = CIBLE.with_suffix(f".bak-{datetime.now():%Y%m%d-%H%M%S}.py")
    shutil.copy2(CIBLE, bak)
    print(f"✅ Backup : {bak.name}")

    nouv = src.replace(ANCRE_IMPORT, NOUVEL_IMPORT, 1)
    nouv = nouv.replace(ANCRE_ADMIN, NOUVEAU_ADMIN, 1)

    try:
        ast.parse(nouv)
    except SyntaxError as e:
        print(f"❌ Syntaxe cassée : {e} — restauration.")
        shutil.copy2(bak, CIBLE)
        sys.exit(1)

    CIBLE.write_text(nouv, encoding="utf-8")
    print("✅ ui.py branché : import + écran admin ?page=plans")
    print(f"   Backup : {bak.name}")
    print()
    print("Redémarrer :")
    print("  pkill -f streamlit; cd ~/mobilite-ia && streamlit run app/api/ui.py")
    print("Puis, connecté en admin, ouvrir :  http://localhost:8501/?page=plans")

if __name__ == "__main__":
    main()
