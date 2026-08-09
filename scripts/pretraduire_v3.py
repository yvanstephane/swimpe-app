#!/usr/bin/env python3
"""
pretraduire_v2.py — Pre-traduit les textes du code. Filtre CORRIGE.

BUG DE LA v1
  _ok() gardait toute chaine contenant >= 2 « mots » de 3+ lettres. Or
  re.findall(r"[a-zA-Z]{3,}", "pwd_hash") -> ['pwd','hash'] : l'underscore
  fait office de separateur. Resultat : pwd_hash, hero_fond, taux_eur:,
  show_auth, client_nom... etaient envoyes au LLM. Sur 1343 « textes »,
  la grande majorite etaient des IDENTIFIANTS DE CODE.

REGLE v2
  Un identifiant de code, c'est une chaine SANS ESPACE composee uniquement
  de [A-Za-z0-9_./:-]. Elle est rejetee. « Sri Lanka », « Cap-Vert »,
  « Code recu » gardent leur espace ou leur accent : ils passent.
  Sont aussi exclus : les fichiers i18n.py / pays_i18n.py (leurs cles sont
  traitees par traduire_i18n.py et traduire_pays.py), les cles de
  st.session_state, les formats %s / {x}, les URL.

Usage (identique a la v1) :
    caffeinate -i python scripts/pretraduire_v2.py de en es pt zh ar ja ko id
    python scripts/pretraduire_v2.py --lister        # montre ce qui passera
"""
import ast
import glob
import re
import sys

sys.path.insert(0, "app/api")

_SKIP = (
    "SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ",
    "WHERE ", "FROM ", "TABLE ", "INDEX ", "PRAGMA",
    "def ", "class ", "return ", "import ", "True", "False",
    "http", "https", "\\n", "%(", ".db", ".py", ".csv",
    "(?", "^[", ".*", "\\s", "\\d",
)
_CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7ff]")

# Un identifiant de code : pas d'espace, et soit il porte _ / : . ,
# soit il est entierement en minuscules. « Cap-Vert » et « Pays-Bas »
# n'ont ni l'un ni l'autre : ce sont des noms propres, ils passent.
_IDENT_PONCT = re.compile(r"^[A-Za-z0-9_./:\-]*[_/:.][A-Za-z0-9_./:\-]*$")
_IDENT_MIN = re.compile(r"^[a-z0-9\-]+$")
# Fichiers dont les chaines sont deja gerees ailleurs
_FICHIERS_EXCLUS = {"i18n.py", "pays_i18n.py"}


def _est_identifiant(s: str) -> bool:
    """pwd_hash, hero_fond, taux_eur:, app/.env, showauth -> True.
    'Sri Lanka', 'Cap-Vert', 'Pays-Bas' -> False."""
    if " " in s:
        return False
    return bool(_IDENT_PONCT.match(s)) or bool(_IDENT_MIN.match(s))


def _ok(s):
    if not isinstance(s, str):
        return False
    s2 = s.strip()
    if len(s2) < 8:
        return False
    if not any(c.isalpha() for c in s2):
        return False
    if s2[0] in ("<", "{", "[", "(", "#"):
        return False
    if _CJK.search(s2):
        return False
    if _est_identifiant(s2):          # <<< LA CORRECTION
        return False
    if "{" in s2 and "}" in s2:       # gabarits f-string / format
        return False
    # CSS / HTML inline : proprietes, balises, styles
    if re.search(r"(text-transform|font-size|background:|border-radius|"
                 r"target=|style=|<[a-z]+ |</[a-z]+>|padding:|margin:|display:)",
                 s2, re.I):
        return False
    # Deja en anglais (description d'offre capturee en dur) : rien a traduire
    # depuis le francais. Heuristique : phrase anglaise sans lettre accentuee
    # et avec des mots-outils anglais typiques.
    if (not re.search(r"[àâäéèêëïîôöùûüçÀ-ÿ]", s2)
            and re.search(r"\b(the|our|your|and|for|with|world|mission|leader)\b",
                          s2, re.I)
            and " " in s2):
        return False
    low = s2.lower()
    if any(k.lower() in low for k in _SKIP):
        return False
    mots = re.findall(r"[a-zA-ZÀ-ÿ]{2,}", s2)
    return len(mots) >= 2


def _ids_docstrings(arbre):
    """id() des noeuds Constant qui sont des docstrings (jamais affichees)."""
    ids = set()
    for n in ast.walk(arbre):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            corps = getattr(n, "body", [])
            if (corps and isinstance(corps[0], ast.Expr)
                    and isinstance(corps[0].value, ast.Constant)
                    and isinstance(corps[0].value.value, str)):
                ids.add(id(corps[0].value))
    return ids


def collecter():
    textes = set()
    for f in sorted(glob.glob("app/api/*.py")):
        if f.rsplit("/", 1)[-1] in _FICHIERS_EXCLUS:
            continue
        try:
            arbre = ast.parse(open(f, encoding="utf-8").read())
        except SyntaxError:
            continue
        docs = _ids_docstrings(arbre)
        for n in ast.walk(arbre):
            if (isinstance(n, ast.Constant) and id(n) not in docs
                    and _ok(n.value)):
                textes.add(n.value.strip())
    return sorted(textes, key=len)


def main():
    if "--lister" in sys.argv:
        t = collecter()
        print(f"{len(t)} textes retenus :\n")
        for s in t:
            print("  •", s[:100])
        return

    from traduction import traduire, _du_cache
    langues = [a for a in sys.argv[1:] if not a.startswith("-")] or ["en"]
    textes = collecter()
    print(f"{len(textes)} textes utiles (filtre v2)")
    for lang in langues:
        deja = sum(1 for t in textes if _du_cache(t, lang) is not None)
        faire = [t for t in textes if _du_cache(t, lang) is None]
        print(f"\n=== {lang} : {deja} en cache, {len(faire)} à traduire ===")
        rates = 0
        for i, t in enumerate(faire, 1):
            r = traduire(t, lang)
            ok = r and r != t
            if not ok:
                rates += 1
            print(f"  [{i}/{len(faire)}] {'✓' if ok else '•'} {t[:60]}")
        print(f"  {'✅ complet' if not rates else f'⚠️ {rates} non traduits — relance'}")


if __name__ == "__main__":
    main()
