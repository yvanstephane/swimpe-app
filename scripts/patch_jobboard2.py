#!/usr/bin/env python3
"""
patch_jobboard2.py — Cinq demandes en un passage, sur des ancres exactes.

  1. DEVISE EN ARRIERE-PLAN : le selecteur sidebar disparait ; les prix
     suivent la destination (devises.py, arrondis) sans intervention.
  2. REFORMULATION honnete et porteuse d'espoir, dans les 6 langues :
        « On t'accompagne jusqu'en X »  ->  « On t'accompagne dans ton
        projet — X ». On promet l'accompagnement, pas l'arrivee.
  3. HERO : DEUX liens de couleurs distinctes a cote du prix —
        or   : 🤝 accompagnement  (?page=accompagnement)
        blanc: 📩 Parle-nous de ton projet  (?page=contact)
     Meme paire en bas de page. Le formulaire du bas RESTE (le CTA des
     offres « Postuler avec notre accompagnement » pointe dessus).
  4. SERVICES PAR TYPE DE PROJET : Bourse n'affiche que les services
     bourse, Metier specialise que les siens, etc. — table SVC_TYPES,
     appliquee au bandeau (prix min), au bloc du bas et a la page dediee.
  5. ROUTEUR v2 : ?page=contact (formulaire seul) + filtre type sur la
     page accompagnement + type transmis dans l'URL.
  + registre.py : charge l'adaptateur mig_de (Allemagne, job board federal).

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_jobboard2.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")
MARQUE = "patch_jobboard2"

resultats: list[str] = []


def ecrire(p: Path, contenu: str, n: int) -> bool:
    if DRY:
        resultats.append(f"~ {p.name} : {n} retouche(s) [DRY-RUN]")
        return True
    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")
    if p.suffix == ".py":
        try:
            ast.parse(contenu)
        except SyntaxError as e:
            shutil.copy2(bak, p)
            resultats.append(f"x {p.name} : syntaxe cassee l.{e.lineno} — restaure")
            return False
    resultats.append(f"v {p.name} : {n} retouche(s) ({bak.name})")
    return True


# =========================================================================== #
# i18n.py — reformulation (6 langues)
# =========================================================================== #
I18N_REMPL = [
    ('"fr":"🤝 On t\'accompagne jusqu\'en", "en":"🤝 We support you all the way to",',
     '"fr":"🤝 On t\'accompagne dans ton projet —", "en":"🤝 We guide you through your project —",'),
    ('"es":"🤝 Te acompañamos hasta", "pt":"🤝 Acompanhamos você até",',
     '"es":"🤝 Te acompañamos en tu proyecto —", "pt":"🤝 Acompanhamos você no seu projeto —",'),
    ('"zh":"🤝 我们全程陪伴你前往", "ar":"🤝 نرافقك حتى"},',
     '"zh":"🤝 我们陪你推进你的项目 —", "ar":"🤝 نرافقك في مشروعك —"},'),
]


def patch_i18n() -> None:
    p = RACINE / "app" / "api" / "i18n.py"
    if not p.exists():
        resultats.append("- i18n.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "dans ton projet —" in src:
        resultats.append("= i18n.py : deja reformule")
        return
    n = 0
    for avant, apres in I18N_REMPL:
        if avant in src:
            src = src.replace(avant, apres, 1)
            n += 1
    if n < 3:
        resultats.append(f"? i18n.py : {n}/3 lignes trouvees — verifie 'accompagne'")
        if n == 0:
            return
    ecrire(p, src, n)


# =========================================================================== #
# sources/registre.py — charger mig_de
# =========================================================================== #
def patch_registre() -> None:
    p = RACINE / "app" / "api" / "sources" / "registre.py"
    if not p.exists():
        resultats.append("- sources/registre.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "mig_de" in src:
        resultats.append("= registre.py : mig_de deja charge")
        return
    ancre = "    from . import adzuna      # noqa: F401"
    if ancre not in src:
        resultats.append("? registre.py : ancre adzuna introuvable")
        return
    src = src.replace(ancre, ancre + "\n"
                      "    try:\n"
                      "        from . import mig_de   # noqa: F401\n"
                      "    except Exception as _e:\n"
                      "        log.warning('mig_de non charge : %s', _e)", 1)
    ecrire(p, src, 1)


# =========================================================================== #
# ui.py — 5 retouches
# =========================================================================== #
A_SIDEBAR = "    devises_cfg.selecteur_sidebar(TAUX)"
R_SIDEBAR = ('    st.session_state.setdefault("devise", "EUR")'
             "  # devise auto par destination — selecteur retire (patch_jobboard2)")

A_DEST = ("# =============================================================================\n"
          "# DESTINATIONS — chaque étape : (titre, détail, lien, code_service_ou_None)")

BLOC_SVC_TYPES = '''# --- Services applicables PAR TYPE DE PROJET (patch_jobboard2) ---------------
# Cle absente = service propose pour tous les types de projet.
SVC_TYPES = {
    "ADMIS":    {"Formation (admission)"},
    "EEF":      {"Formation (admission)"},
    "PACK":     {"Formation (admission)"},
    "ORIENT":   {"Formation (admission)", "Bourse"},
    "BOURSE":   {"Formation (admission)", "Bourse"},
    "FONDS":    {"Formation (admission)", "Stage / Emploi étudiant"},
    "VISA":     {"Formation (admission)", "Stage / Emploi étudiant", "Métier spécialisé"},
    "LOGEMENT": {"Formation (admission)", "Stage / Emploi étudiant", "Métier spécialisé"},
}


def _services_pour_type(codes, type_projet):
    """Ne garde que les services pertinents pour CE type de projet.
    Repli : si le filtre vide tout, on rend la liste d'origine."""
    filt = [s for s in codes if type_projet in SVC_TYPES.get(s, {type_projet})]
    return filt or list(codes)


'''

A_PRIX = "    _prix = services_cfg.tarifs_tous({k: v[2] for k, v in SVC.items()})"
R_PRIX = ("    services_dest = _services_pour_type(services_dest, type_c)"
          "  # patch_jobboard2\n" + A_PRIX)

A_URL = ('''    _url_acc = ("?page=accompagnement&dest=" + destination + "&lg=" + LG
                + "&orig=" + _up.quote(origine or ""))''')
R_URL = ('''    _url_acc = ("?page=accompagnement&dest=" + destination + "&lg=" + LG
                + "&orig=" + _up.quote(origine or "")
                + "&type=" + _up.quote(type_c or ""))
    _url_contact = _url_acc.replace("page=accompagnement", "page=contact")''')

A_HERO = ("  <a class='prix' href='{_url_acc}' target='_blank' "
          "style='text-decoration:none; margin-left:.6rem;'>"
          "🤝 {t('accompagne', LG)} {nom_pays(d['nom'], LG)} →</a>")
R_HERO = (
    "  <a href='{_url_acc}' target='_blank' style='text-decoration:none; "
    "margin-left:.6rem; background:#e9b949; color:#1f2937; "
    "padding:.4rem .9rem; border-radius:999px; font-weight:700; "
    "display:inline-block;'>🤝 {t('accompagne', LG)} "
    "{nom_pays(d['nom'], LG)} →</a>\n"
    "  <a href='{_url_contact}' target='_blank' style='text-decoration:none; "
    "margin-left:.5rem; background:#ffffff; color:#1f2937; "
    "padding:.4rem .9rem; border-radius:999px; font-weight:700; "
    "display:inline-block;'>{t('form_titre', LG).split('—')[0].strip()} →</a>"
)

A_BAS = ('''    st.link_button("🤝 " + t("accompagne", LG) + " " + nom_pays(d["nom"], LG) + " →",
                   _url_acc, use_container_width=True)''')
R_BAS = ('''    _cA, _cB = st.columns(2)
    _cA.link_button("🤝 " + t("accompagne", LG) + " " + nom_pays(d["nom"], LG) + " →",
                    _url_acc, use_container_width=True)
    _cB.link_button(t("form_titre", LG).split("—")[0].strip() + " →",
                    _url_contact, use_container_width=True)''')

# ---- Routeur v2 : remplace INTEGRALEMENT le bloc du patch precedent -------- #
R_DEBUT = "# --- Page dediee « Accompagnement » (patch_accompagnement) ------------------"
R_FIN = "# -----------------------------------------------------------------------------"

ROUTEUR_V2 = '''# --- Pages dediees « accompagnement » et « contact » (patch_jobboard2) ------
# Un NOUVEL ONGLET = une nouvelle session : le contexte arrive par l'URL.
#   ?page=accompagnement&dest=DE&lg=fr&orig=Benin&type=M%C3%A9tier%20sp%C3%A9cialis%C3%A9
_qp = st.query_params
if _qp.get("page") in ("accompagnement", "contact"):
    import urllib.parse as _up
    _tr = globals().get("tr", lambda s: s)
    _lg_qp = _qp.get("lg") or ""
    if _lg_qp in LANGUES and _lg_qp != LG:
        st.session_state.lang = _lg_qp
        LG = _lg_qp
    _dst = (_qp.get("dest") or "").upper()
    _type_qp = _up.unquote(_qp.get("type") or "")
    _d = D.get(_dst)
    if not _d:
        st.warning("🌍 " + _tr("Choisis d'abord un pays de destination sur la page principale."))
        st.link_button("← Yorbity", "/")
        st.stop()

    try:
        import theme_pays
        theme_pays.appliquer(_dst, theme_pays.type_interne(_type_qp), _tr)
    except Exception:
        pass

    _svc_dest = (services_cfg.effectifs(_dst, _d["services"], list(SVC.keys()))
                 or _d["services"])
    if _type_qp:
        _svc_dest = _services_pour_type(_svc_dest, _type_qp)
    _noms = []

    if _qp.get("page") == "accompagnement":
        st.markdown(f"## {t('accompagne', LG)} {nom_pays(_d['nom'], LG)}")
        st.write(t("accompagne_desc", LG))
        for _s in _svc_dest:
            _n, _de, _ = SVC[_s]
            _n, _de = _tr(_n), _tr(_de)
            _noms.append(_n)
            with st.expander(_n):
                st.write(_de)
    else:
        _noms = [_tr(SVC[_s][0]) for _s in _svc_dest]

    st.markdown("#### " + t("form_titre", LG))
    with st.form("lead_page_dediee"):
        _f1, _f2 = st.columns(2)
        _nom_lead = _f1.text_input(t("nom", LG))
        _contact = _f2.text_input(t("contact", LG))
        _svc_choisi = st.selectbox(t("service_interet", LG), _noms)
        _msg = st.text_area(t("projet_2lignes", LG))
        if st.form_submit_button(t("lancer", LG)):
            if _nom_lead.strip() and _contact.strip():
                con.execute(
                    "INSERT INTO leads(date,nom,contact,origine,destination,service,message) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (TODAY, _nom_lead.strip(), _contact.strip(),
                     _up.unquote(_qp.get("orig") or ""), _d["nom"],
                     _svc_choisi, _msg.strip()))
                con.commit()
                st.success("✅ " + _tr("Merci ! Notre équipe te répond sous 24 h."))
            else:
                st.error(_tr("Nom et contact sont obligatoires."))
    st.caption(_tr("Nous préparons et organisons tes démarches avec toi. "
                   "Personne ne peut garantir une admission ou un visa — "
                   "méfie-toi de ceux qui le promettent."))
    st.stop()
# -----------------------------------------------------------------------------'''


def patch_ui() -> None:
    p = RACINE / "app" / "api" / "ui.py"
    if not p.exists():
        resultats.append("- ui.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if MARQUE in src:
        resultats.append("= ui.py : deja patche")
        return

    ancres = {"sidebar": A_SIDEBAR, "destinations": A_DEST, "prix": A_PRIX,
              "url": A_URL, "hero": A_HERO, "bas": A_BAS,
              "routeur-debut": R_DEBUT, "routeur-fin": R_FIN}
    absentes = [n for n, a in ancres.items() if a not in src]
    if absentes:
        resultats.append(f"? ui.py : ancres absentes {absentes} — RIEN ECRIT")
        return

    n = 0
    src = src.replace(A_SIDEBAR, R_SIDEBAR, 1); n += 1
    src = src.replace(A_DEST, BLOC_SVC_TYPES + A_DEST, 1); n += 1
    src = src.replace(A_PRIX, R_PRIX, 1); n += 1
    src = src.replace(A_URL, R_URL, 1); n += 1
    src = src.replace(A_HERO, R_HERO, 1); n += 1
    src = src.replace(A_BAS, R_BAS, 1); n += 1

    i_deb = src.index(R_DEBUT)
    i_fin = src.index(R_FIN, i_deb) + len(R_FIN)
    src = src[:i_deb] + ROUTEUR_V2 + src[i_fin:]; n += 1

    ecrire(p, src, n)


# =========================================================================== #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    patch_i18n()
    patch_registre()
    patch_ui()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith(("x", "?")) for r in resultats):
        print("\nATTENTION : voir les lignes ? / x ci-dessus.")
        sys.exit(2)
    print("\nFINI — relance : yorbity")


if __name__ == "__main__":
    main()
