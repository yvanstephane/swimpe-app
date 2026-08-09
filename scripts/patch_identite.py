#!/usr/bin/env python3
"""
patch_identite.py — L'abonnement est PERSONNEL : verrou nominatif.

Constat (comptes.txt) : la table dossiers n'a PAS de champ nom — un dossier
est soude a user_id, et l'admin voit le nom DU COMPTE. Le scenario
« Thibault cree un dossier pour Helene » est donc deja structurellement
impossible cote dossiers. Le maillon a verrouiller est le NOM DU COMPTE.

  1. auth.inscrire()   : le nom doit etre un nom complet plausible
                         (prenom + nom, lettres seulement) — sinon refus
                         avec message. Espaces normalises au stockage.
  2. espace.py         : sous le champ nom du formulaire d'inscription,
                         mention claire : abonnement personnel, dossiers
                         ouverts a ce nom uniquement.
  3. dossiers.creer()  : garde-fou pour tout code FUTUR — un parametre
                         beneficiaire optionnel, compare au nom du compte
                         (accents/casse/ordre neutralises via identite.py) ;
                         refuse si different, sauf autorise_tiers=True
                         (reserve aux ecrans admin).
  4. i18n.py           : cle nom_legal_note en 7 langues.

Prerequis : app/api/identite.py (livre ensemble).
Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_identite.py [--dry]
"""
from __future__ import annotations

import ast
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")

resultats: list[str] = []


def ecrire(p: Path, contenu: str, n: int) -> bool:
    if DRY:
        resultats.append(f"~ {p.name} : {n} retouche(s) [DRY-RUN]")
        return True
    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")
    try:
        ast.parse(contenu)
    except SyntaxError as e:
        shutil.copy2(bak, p)
        resultats.append(f"x {p.name} : syntaxe cassee l.{e.lineno} — restaure")
        return False
    resultats.append(f"v {p.name} : {n} retouche(s) ({bak.name})")
    return True


# =========================================================================== #
# auth.py
# =========================================================================== #
A_AUTH_VALID = """    err = _valide_pwd(pwd)
    if err:
        return False, err"""
R_AUTH_VALID = """    err = _valide_pwd(pwd)
    if err:
        return False, err
    # Abonnement PERSONNEL : le nom du compte est un nom legal complet
    # (patch_identite). Les dossiers ne peuvent etre ouverts qu'a ce nom.
    try:
        import identite
        ok_nom, err_nom = identite.valider_nom_complet(nom)
        if not ok_nom:
            return False, err_nom
    except ImportError:
        pass"""

A_AUTH_STORE = '(email, nom.strip(), pays_origine, telephone.strip(), h, salt, "etudiant",'
R_AUTH_STORE = '(email, " ".join((nom or "").split()), pays_origine, telephone.strip(), h, salt, "etudiant",'


def patch_auth() -> None:
    p = RACINE / "app" / "api" / "auth.py"
    if not p.exists():
        resultats.append("- auth.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "valider_nom_complet" in src:
        resultats.append("= auth.py : deja patche")
        return
    n = 0
    if A_AUTH_VALID in src:
        src = src.replace(A_AUTH_VALID, R_AUTH_VALID, 1); n += 1
    else:
        resultats.append("? auth.py : bloc de validation introuvable")
    if A_AUTH_STORE in src:
        src = src.replace(A_AUTH_STORE, R_AUTH_STORE, 1); n += 1
    else:
        resultats.append("? auth.py : ligne INSERT introuvable")
    if n:
        ecrire(p, src, n)


# =========================================================================== #
# dossiers.py
# =========================================================================== #
A_CREER = '''def creer(user_id, service, destination):
    init_db()
    auj = datetime.date.today().isoformat()
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO dossiers(user_id,service,destination,cree_le,maj_le) "
                "VALUES(?,?,?,?,?)", (user_id, service, destination, auj, auj))
    con.commit(); con.close()'''

R_CREER = '''def creer(user_id, service, destination, beneficiaire=None,
          autorise_tiers=False):
    """Cree un dossier pour LE TITULAIRE du compte.

    Abonnement personnel (patch_identite) : si un code futur passe un
    `beneficiaire`, il doit designer la meme personne que le compte
    (accents, casse et ordre des mots neutralises). `autorise_tiers=True`
    est reserve aux ecrans admin.
    Retourne (True, "") ou (False, message). Les appels existants qui
    ignorent le retour restent valides.
    """
    init_db()
    con = sqlite3.connect(DB)
    try:
        row = con.execute("SELECT nom FROM users WHERE id=?",
                          (user_id,)).fetchone()
        if not row:
            return False, "Compte introuvable."
        if beneficiaire and not autorise_tiers:
            try:
                import identite
                if not identite.meme_personne(beneficiaire, row[0] or ""):
                    return False, (
                        "Ton abonnement est personnel : les dossiers sont "
                        f"ouverts au nom du compte ({row[0]}). Pour une autre "
                        "personne, elle doit creer son propre compte.")
            except ImportError:
                pass
        auj = datetime.date.today().isoformat()
        con.execute("INSERT INTO dossiers(user_id,service,destination,cree_le,maj_le) "
                    "VALUES(?,?,?,?,?)", (user_id, service, destination, auj, auj))
        con.commit()
        return True, ""
    finally:
        con.close()'''


def patch_dossiers() -> None:
    p = RACINE / "app" / "api" / "dossiers.py"
    if not p.exists():
        resultats.append("- dossiers.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "autorise_tiers" in src:
        resultats.append("= dossiers.py : deja patche")
        return
    if A_CREER not in src:
        resultats.append("? dossiers.py : fonction creer() introuvable a l'identique")
        return
    src = src.replace(A_CREER, R_CREER, 1)
    ecrire(p, src, 1)


# =========================================================================== #
# espace.py — mention sous le champ nom
# =========================================================================== #
A_ESPACE = '            nom = st.text_input(t("champ_nom", _lg()))'
R_ESPACE = ('            nom = st.text_input(t("champ_nom", _lg()))\n'
            '            st.caption("🪪 " + t("nom_legal_note", _lg()))')


def patch_espace() -> None:
    p = RACINE / "app" / "api" / "espace.py"
    if not p.exists():
        resultats.append("- espace.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "nom_legal_note" in src:
        resultats.append("= espace.py : deja patche")
        return
    if A_ESPACE not in src:
        resultats.append("? espace.py : champ nom introuvable")
        return
    src = src.replace(A_ESPACE, R_ESPACE, 1)
    ecrire(p, src, 1)


# =========================================================================== #
# i18n.py — cle nom_legal_note (7 langues)
# =========================================================================== #
CLE_I18N = ''' "nom_legal_note": {
   "fr":"Ton nom complet, comme sur ton passeport — ton abonnement est personnel : tes dossiers seront ouverts à ce nom uniquement.",
   "en":"Your full name, as on your passport — your subscription is personal: files are opened under this name only.",
   "es":"Tu nombre completo, como en tu pasaporte — tu suscripción es personal: los expedientes se abren solo a este nombre.",
   "pt":"Seu nome completo, como no passaporte — sua assinatura é pessoal: os dossiês são abertos apenas neste nome.",
   "de":"Dein vollständiger Name wie im Pass — dein Abo ist persönlich: Dossiers werden nur auf diesen Namen eröffnet.",
   "zh":"你的全名（与护照一致）— 订阅仅限本人：档案只能以此姓名开立。",
   "ar":"اسمك الكامل كما في جواز السفر — اشتراكك شخصي: تُفتح الملفات بهذا الاسم فقط."},
'''


def patch_i18n() -> None:
    p = RACINE / "app" / "api" / "i18n.py"
    if not p.exists():
        resultats.append("- i18n.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "nom_legal_note" in src:
        resultats.append("= i18n.py : cle deja presente")
        return
    m = re.search(r"^T\s*=\s*\{\s*\n", src, re.M)
    if not m:
        resultats.append("? i18n.py : dict T introuvable — cle non ajoutee")
        return
    src = src[:m.end()] + CLE_I18N + src[m.end():]
    ecrire(p, src, 1)


# =========================================================================== #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    if not (RACINE / "app" / "api" / "identite.py").exists() and not DRY:
        print("!! app/api/identite.py manquant — installe-le d'abord.")
        sys.exit(1)
    patch_auth()
    patch_dossiers()
    patch_espace()
    patch_i18n()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        print("\nATTENTION : certaines retouches sautees (voir ?).")
        sys.exit(2)
    print("\nFINI — pkill -f streamlit ; puis : yorbity")


if __name__ == "__main__":
    main()
