"""
sources/registre.py — Assemble les adaptateurs et les selectionne par
(destination, type_projet).

offres_sync.ingerer() n'a plus a connaitre Job Bank ni Adzuna :

    for src in registre.sources_pour("CA", "emploi"):
        for offre in src.collecter("CA", "emploi"):
            ...

Activation/desactivation : on reutilise param()/definir_param() de offres_sync,
qui existent deja. Pas de seconde base de reglages.
Cle : "source_active:<nom>"  ->  "1" | "0"
"""

from __future__ import annotations

import logging

from .base import SourceOffres, TYPES_PROJET

log = logging.getLogger("yorbity.sources")

_REGISTRE: dict[str, SourceOffres] = {}


# --------------------------------------------------------------------------- #
# Enregistrement
# --------------------------------------------------------------------------- #
def enregistrer(source: SourceOffres) -> None:
    if not source.nom:
        raise ValueError("Une source doit avoir un attribut `nom`.")
    for t in source.types_projet:
        if t not in TYPES_PROJET:
            raise ValueError(f"{source.nom}: type_projet inconnu {t!r}")
    if source.nom in _REGISTRE:
        log.warning("Source %s deja enregistree, remplacee.", source.nom)
    _REGISTRE[source.nom] = source
    log.info("Source enregistree : %r", source)


def toutes() -> dict[str, SourceOffres]:
    return dict(_REGISTRE)


def par_nom(nom: str) -> SourceOffres | None:
    return _REGISTRE.get(nom)


# --------------------------------------------------------------------------- #
# Activation (s'appuie sur offres_sync.param, deja en place)
# --------------------------------------------------------------------------- #
def _param(cle: str, defaut: str = "") -> str:
    try:
        import offres_sync
        return offres_sync.param(cle, defaut)
    except Exception:
        return defaut


def _definir_param(cle: str, valeur: str) -> None:
    try:
        import offres_sync
        offres_sync.definir_param(cle, valeur)
    except Exception as e:
        log.warning("Impossible d'ecrire le parametre %s : %s", cle, e)


def est_active(nom: str) -> bool:
    return _param(f"source_active:{nom}", "1") != "0"


def definir_active(nom: str, active: bool) -> None:
    _definir_param(f"source_active:{nom}", "1" if active else "0")


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #
def sources_pour(
    destination: str,
    type_projet: str | None = None,
    sans_permis: bool | None = None,
) -> list[SourceOffres]:
    """
    sans_permis=True  -> ne renvoie que les sources dont ce (pays, type) est
                         accessible a un candidat sans permis de travail.
                         C'est ce filtre qui evite de promettre a un etudiant
                         reste au pays un emploi qu'il ne peut pas prendre.
    """
    out = []
    for s in _REGISTRE.values():
        if not est_active(s.nom):
            continue
        if not s.couvre(destination, type_projet):
            continue
        if not s.disponible():
            log.info("Source %s indisponible (cles absentes ?).", s.nom)
            continue
        if sans_permis is not None and type_projet is not None:
            if s.admissible_sans_permis(destination, type_projet) != sans_permis:
                continue
        out.append(s)
    return out


def destinations_couvertes() -> set[str]:
    d: set[str] = set()
    for s in _REGISTRE.values():
        d.update(s.destinations)
    return d


_EXTRAIT_TRAD = 600


def _traduire_offre(od: dict, lang: str) -> None:
    """Traduit titre + debut d'extrait dans la langue de l'interface via le
    pipeline maison (cache SQLite, petit modele rapide OFFRES_MODEL) —
    patch_offres. Le bandeau 🛂 (deja localise) est preserve. Le moindre
    pepin laisse l'offre telle quelle."""
    try:
        if not lang:
            try:
                import streamlit as st
                lang = st.session_state.get("lang", "")
            except Exception:
                return
        if not lang or lang == od.get("langue_source"):
            return
        import os

        import traduction
        if not hasattr(traduction, "traduire_vers"):
            return
        modele = os.environ.get("OFFRES_MODEL", "llama3.2:3b")
        titre = od.get("titre") or ""
        if titre:
            od["titre"] = traduction.traduire_vers(titre, lang, modele)
        ex = od.get("extrait") or ""
        if not ex:
            return
        pre = ""
        if ex.startswith("🛂"):
            coupe = ex.find("\n\n")
            if coupe > 0:
                pre, ex = ex[:coupe + 2], ex[coupe + 2:]
        tete, reste = ex[:_EXTRAIT_TRAD], ex[_EXTRAIT_TRAD:]
        od["extrait"] = (pre + traduction.traduire_vers(tete, lang, modele)
                         + ("\n\n[…]" if reste else ""))
    except Exception:
        pass


def collecter_page(
    destination: str,
    type_projet: str,
    mots_cles: str | None = None,
    page: int = 1,
    par_page: int = 8,
    lang: str = "en",
    sans_permis: bool | None = None,
) -> tuple[list[dict], int]:
    """
    Une PAGE d'offres, toutes sources confondues, et le total disponible.

    Les sources sont interrogees dans l'ordre de priorite (postulables + liens
    accessibles d'abord). Chaque source pagine chez elle : on demande la meme
    page a chacune, puis on concatene en respectant l'ordre. Le total est la
    somme des totaux — c'est une approximation haute (la dedup inter-sources
    peut retirer quelques doublons), suffisante pour un compteur "sur ~N".
    """
    srcs = sources_pour(destination, type_projet, sans_permis)
    srcs.sort(key=lambda s: (
        not s.admissible_sans_permis(destination, type_projet),
        not s.lien_accessible_depuis_etranger(destination, type_projet),
    ))

    vus: set[str] = set()
    offres: list[dict] = []
    total = 0
    for s in srcs:
        accessible = s.lien_accessible_depuis_etranger(destination, type_projet)
        try:
            lot, n = s.collecter_page(destination, type_projet, mots_cles,
                                      page, par_page, lang)
        except Exception as e:
            log.error("Source %s en erreur (page %s) : %s", s.nom, page, e)
            continue
        total += n
        for o in lot:
            if o.url in vus:
                continue
            vus.add(o.url)
            od = o.to_dict()
            od["lien_accessible"] = accessible
            _traduire_offre(od, lang)          # patch_offres
            offres.append(od)

    log.info("page %s : %s offres sur ~%s pour %s/%s",
             page, len(offres), total, destination, type_projet)
    return offres, total


def collecter(
    destination: str,
    type_projet: str,
    mots_cles: str | None = None,
    limite: int = 50,
    lang: str = "en",
    sans_permis: bool | None = None,
) -> list[dict]:
    """
    Interroge toutes les sources pertinentes, deduplique sur l'URL.

    Ordre : d'abord les sources dont les offres sont postulables sans permis
    ET dont les liens s'ouvrent depuis l'etranger (ex. Job Bank), ensuite les
    catalogues (ex. Adzuna). Chaque offre porte `lien_accessible` : l'UI
    masque le lien au visiteur quand il est False, l'admin le voit toujours.
    """
    srcs = sources_pour(destination, type_projet, sans_permis)
    srcs.sort(key=lambda s: (
        not s.admissible_sans_permis(destination, type_projet),
        not s.lien_accessible_depuis_etranger(destination, type_projet),
    ))

    vus: set[str] = set()
    offres: list[dict] = []
    for s in srcs:
        accessible = s.lien_accessible_depuis_etranger(destination, type_projet)
        try:
            lot = s.collecter(destination, type_projet, mots_cles, limite, lang)
        except Exception as e:
            log.error("Source %s en erreur : %s", s.nom, e)
            continue
        for o in lot:
            if o.url in vus:
                continue
            vus.add(o.url)
            od = o.to_dict()
            od["lien_accessible"] = accessible
            offres.append(od)
    log.info("%s: %s offres pour %s/%s", __name__, len(offres), destination, type_projet)
    return offres


# --------------------------------------------------------------------------- #
# Chargement des adaptateurs
# --------------------------------------------------------------------------- #
def charger_defaut() -> None:
    """Importe les adaptateurs livres. Chacun s'enregistre a l'import."""
    from . import jobbank_ca  # noqa: F401
    from . import adzuna      # noqa: F401
    try:
        from . import mig_de   # noqa: F401
    except Exception as _e:
        log.warning('mig_de non charge : %s', _e)
    try:
        from . import uk_sponsors   # noqa: F401
    except Exception as _e:
        log.warning('uk_sponsors non charge : %s', _e)
    # from . import pole_emploi_fr


charger_defaut()
