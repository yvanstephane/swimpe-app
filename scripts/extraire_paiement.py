#!/usr/bin/env python3
"""Imprime paiement.py en entier + les points de branchement dans ui.py."""
from pathlib import Path
RACINE = Path(__file__).resolve().parent
API = RACINE / "app" / "api"

def montrer(nom):
    p = API / nom
    print("\n" + "#"*70 + f"\n# {nom}\n" + "#"*70)
    if not p.exists():
        print("  [absent]"); return
    for i, l in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        print(f"{i:5d}| {l}")

montrer("paiement.py")

# points de branchement dans ui.py
print("\n" + "#"*70 + "\n# ui.py — appels paiement / premium / CinetPay\n" + "#"*70)
ui = (API / "ui.py").read_text(encoding="utf-8", errors="ignore").splitlines()
import re
for i, l in enumerate(ui):
    if re.search(r"paiement|cinetpay|premium|activer_premium|paiement_retour", l, re.I):
        for k in range(max(0,i-2), min(len(ui), i+3)):
            print(f"{k+1:5d}| {ui[k]}")
        print("     " + "-"*40)
