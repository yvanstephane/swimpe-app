import re
#!/usr/bin/env python3
import ast, os, sys, glob
sys.path.insert(0, "app/api")
from traduction import traduire, _du_cache

_SKIP = (
    "SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ",
    "WHERE ", "FROM ", "TABLE ", "INDEX ", "PRAGMA",
    "def ", "class ", "return ", "import ", "True", "False",
    "http", "https", "\\n", "%(", ".db", ".py", ".csv",
    "(?", "^[", ".*", "\\s", "\\d",
)
_CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7ff]")

def _ok(s):
    if not isinstance(s, str): return False
    s2 = s.strip()
    if len(s2) < 8: return False
    if not any(c.isalpha() for c in s2): return False
    if s2[0] in ("<", "{", "[", "(", "#"): return False
    if _CJK.search(s2): return False
    low = s2.lower()
    if any(k.lower() in low for k in _SKIP): return False
    # garder seulement si contient un mot français ou un emoji suivi de texte
    mots_fr = sum(1 for w in re.findall(r"[a-zA-ZÀ-ÿ]{3,}", s2))
    return mots_fr >= 2

def collecter():
    textes = set()
    for f in sorted(glob.glob("app/api/*.py")):
        try: arbre = ast.parse(open(f, encoding="utf-8").read())
        except SyntaxError: continue
        for n in ast.walk(arbre):
            if isinstance(n, ast.Constant) and _ok(n.value):
                textes.add(n.value.strip())
    return sorted(textes, key=len)

def main():
    
    langues = sys.argv[1:] or ["en"]
    textes = collecter()
    print(f"{len(textes)} textes utiles (filtrés)")
    for lang in langues:
        deja = sum(1 for t in textes if _du_cache(t, lang) is not None)
        faire = [t for t in textes if _du_cache(t, lang) is None]
        print(f"\n=== {lang} : {deja} en cache, {len(faire)} à traduire ===")
        rates = 0
        for i, t in enumerate(faire, 1):
            r = traduire(t, lang)
            ok = r and r != t
            if not ok: rates += 1
            print(f"  [{i}/{len(faire)}] {'✓' if ok else '•'} {t[:60]}")
        print(f"  {'✅ complet' if not rates else f'⚠️ {rates} non traduits — relance'}")

if __name__ == "__main__":
    main()
