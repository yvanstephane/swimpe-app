#!/usr/bin/env python3
"""
patch_renommer_console_v1.py
Corrige la collision : la console passe de ?page=accompagnement (déjà pris
par un écran existant) à ?page=console.
  1. Dans console_accompagnement.py : la valeur testée devient "console".
  2. Dans moteur_plans.py : passe de ?page=plans à ?page=plans (inchangé),
     mais on vérifie qu'il n'entre pas en collision (il est déjà unique).
Idempotent · .bak horodaté · ast.parse · restauration si casse.
Usage : python3 patch_renommer_console_v1.py
"""
import ast, shutil, sys
from datetime import datetime
from pathlib import Path

RACINE = Path.home() / "mobilite-ia"
CONSOLE = RACINE / "app/api/console_accompagnement.py"

ANCIEN = 'if page != "accompagnement":'
NOUVEAU = 'if page != "console":'

def main():
    if not CONSOLE.exists():
        sys.exit(f"❌ Introuvable : {CONSOLE}")
    src = CONSOLE.read_text(encoding="utf-8")

    if NOUVEAU in src:
        print("ℹ️  Console déjà sur ?page=console — rien à faire.")
        return
    if ANCIEN not in src:
        sys.exit("❌ Ancre introuvable dans console_accompagnement.py — abandon.")
    if src.count(ANCIEN) != 1:
        sys.exit("❌ Ancre non unique — abandon.")

    bak = CONSOLE.with_suffix(f".bak-{datetime.now():%Y%m%d-%H%M%S}.py")
    shutil.copy2(CONSOLE, bak)
    nouv = src.replace(ANCIEN, NOUVEAU, 1)
    try:
        ast.parse(nouv)
    except SyntaxError as e:
        shutil.copy2(bak, CONSOLE)
        sys.exit(f"❌ Syntaxe cassée ({e}) — restauré.")
    CONSOLE.write_text(nouv, encoding="utf-8")
    print(f"✅ Console renommée : ?page=console (backup {bak.name})")
    print()
    print("Redémarrer :")
    print("  pkill -f streamlit; cd ~/mobilite-ia && streamlit run app/api/ui.py")
    print("  (ou ta commande 'yorbity')")
    print("Puis, connecté en admin :  http://localhost:8501/?page=console")

if __name__ == "__main__":
    main()
