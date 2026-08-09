# =============================================================================
# traduction.py — Traduction automatique du CONTENU (fiches pays, services)
# via le LLM local Ollama (llama3.3:70b). Résultats mis en cache dans SQLite
# pour ne traduire qu'une seule fois chaque texte.
# =============================================================================
import sqlite3, hashlib, os, json, urllib.request

DB = "data/mobilite.db"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL  = os.environ.get("MAIN_MODEL", "llama3.3:70b-instruct-q4_K_M")

# Noms complets des langues pour le prompt
LANGUE_NOM = {
    "en":"anglais","es":"espagnol","pt":"portugais","zh":"chinois (simplifié)",
    "ar":"arabe","ja":"japonais","ko":"coréen","id":"indonésien",
    "de":"allemand","it":"italien",
}


def nom_langue(lang):
    """Nom francais de la langue cible (patch_fixpack). Secours CLDR via
    Babel pour toute langue future ; None = langue inconnue -> on ne
    traduit pas plutot que d'envoyer un code brut au modele."""
    if lang in LANGUE_NOM:
        return LANGUE_NOM[lang]
    try:
        from babel import Locale
        n = Locale(lang).get_display_name("fr")
        if n and n.lower() != lang.lower():
            return n
    except Exception:
        pass
    return None


# Marqueurs EXCLUSIVEMENT francais (absents de l'italien, l'allemand,
# l'espagnol...) : s'ils abondent, la « traduction » est restee en francais.
_STOP_FR = (" vous ", " tes ", " c'est ", " d'un ", " aux ",
            " avec ", " pour ", " être ")


def _semble_francais(texte, lang):
    if lang == "fr" or not texte:
        return False
    t = " " + texte.lower().replace("\u2019", "'") + " "
    return sum(t.count(s) for s in _STOP_FR) >= 2

def _init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS trad_cache(
        cle TEXT PRIMARY KEY, texte_fr TEXT, lang TEXT, traduction TEXT)""")
    con.commit(); con.close()

def _cle(texte, lang):
    return hashlib.md5((lang + "::" + texte).encode()).hexdigest()

def _du_cache(texte, lang):
    _init()
    con = sqlite3.connect(DB)
    row = con.execute("SELECT traduction FROM trad_cache WHERE cle=?",
                      (_cle(texte, lang),)).fetchone()
    con.close()
    return row[0] if row else None

def _au_cache(texte, lang, trad):
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO trad_cache(cle,texte_fr,lang,traduction) VALUES(?,?,?,?)",
                (_cle(texte, lang), texte, lang, trad))
    con.commit(); con.close()

def _appel_ollama(texte, lang, model=None):
    """Traduit un texte français via Ollama. Retourne None si Ollama indisponible."""
    langue = nom_langue(lang)
    if not langue:                      # patch_fixpack : jamais de code brut
        return None
    prompt = (f"Traduis le texte suivant du français vers le {langue}. "
              f"Réponds UNIQUEMENT dans cette langue ({langue}), jamais en français. "
              f"Garde exactement le même sens, le même ton, et les mêmes montants, "
              f"noms propres et sigles (ex : Campus France, AVI, FCFA, EEF restent tels quels). "
              f"Ne rajoute AUCUN commentaire, réponds UNIQUEMENT avec la traduction.\n\n"
              f"Texte : {texte}")
    try:
        payload = json.dumps({
            "model": model or MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.2}
        }).encode()
        req = urllib.request.Request(f"{OLLAMA}/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        rep = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return rep.get("response", "").strip()
    except Exception:
        return None

def _generer(prompt, model=None):
    """Appel Ollama brut (patch_offres) : prompt libre, modele au choix."""
    try:
        payload = json.dumps({
            "model": model or MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.2}
        }).encode()
        req = urllib.request.Request(f"{OLLAMA}/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        rep = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return rep.get("response", "").strip()
    except Exception:
        return None


def traduire_vers(texte, lang, model=None):
    """Comme traduire(), mais SANS supposer que la source est le francais
    (patch_offres) : sert aux offres d'emploi (allemand/anglais -> langue
    de l'interface, y compris le francais). Meme cache, memes garde-fous."""
    if not texte or not lang:
        return texte
    cache = _du_cache(texte, lang)
    if cache is not None:
        return cache
    langue = nom_langue(lang) or ("français" if lang == "fr" else None)
    if not langue:
        return texte
    prompt = (f"Traduis le texte suivant vers le {langue}. "
              f"Réponds UNIQUEMENT dans cette langue ({langue}). "
              f"Garde le même sens, les montants, noms propres et sigles. "
              f"Aucun commentaire, uniquement la traduction.\n\nTexte : {texte}")
    trad = _generer(prompt, model)
    if trad and trad.strip() != texte.strip() and not _semble_francais(trad, lang):
        _au_cache(texte, lang, trad)
        return trad
    return texte


def traduire(texte, lang):
    """Traduit un texte (avec cache). Si lang=fr ou texte vide, renvoie tel quel.
    Si Ollama est indisponible, renvoie le texte français (repli sûr)."""
    if not texte or lang == "fr":
        return texte
    cache = _du_cache(texte, lang)
    if cache is not None:
        return cache
    trad = _appel_ollama(texte, lang)  # (modele principal)
    if trad and trad.strip() != texte.strip() and not _semble_francais(trad, lang):
        _au_cache(texte, lang, trad)    # patch_fixpack : jamais de francais
        return trad                     # ni d'echo en cache
    return texte   # repli : français si le LLM local n'est pas dispo

# ----------------------------------------------------------------------------
# Pré-traduction en masse (à lancer depuis le terminal pour tout traduire
# d'avance, une bonne fois, dans une langue donnée)
#   python app/api/traduction.py en
# ----------------------------------------------------------------------------
def pretraduire_tout(lang):
    """Traduit d'avance tous les textes des fiches pays + services dans une langue."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    # On importe D et SVC depuis ui.py serait lourd ; on relit les textes depuis
    # un export. Ici, approche simple : l'app traduit à la volée + met en cache.
    print(f"Pour pré-traduire, ouvre l'app et navigue dans les fiches en {lang} :")
    print("chaque fiche consultée est traduite puis mise en cache automatiquement.")
    print("Alternative : lance ce script avec la liste de textes à traduire.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        lang = sys.argv[1]
        # Test rapide de connexion à Ollama
        essai = _appel_ollama("Bonjour, ceci est un test.", lang)
        if essai:
            print(f"✓ Ollama répond. Exemple ({lang}) : {essai[:80]}")
        else:
            print("✗ Ollama ne répond pas. Vérifie qu'il tourne : ollama serve")
    else:
        print("Usage : python app/api/traduction.py <lang>  (en, es, pt, zh, ar, ja, ko, id)")
