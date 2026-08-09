"""
sources/uk_sponsors.py — Angleterre : offres Adzuna gb FILTREES par le
registre officiel des sponsors du Home Office.

LE « fglo=1 » BRITANNIQUE
  Le Royaume-Uni n'a pas de job board public avec filtre international,
  mais il publie LA liste officielle des employeurs habilites a
  sponsoriser un visa de travail (Register of licensed sponsors, CSV
  mensuel sur gov.uk). Croiser Adzuna gb avec ce registre donne le seul
  sous-ensemble d'offres ou l'employeur PEUT legalement recruter un
  candidat international.

HONNETETE
  Employeur au registre = habilite a sponsoriser, PAS engagement a le
  faire pour ce poste. D'ou sans_permis = True assorti d'un bandeau
  explicite dans chaque extrait (licence + seuil Skilled Worker ~25 000
  GBP + decision finale a l'employeur). Liens Adzuna : substitues hors
  du domaine national (comme DE/ES) -> lien_accessible False, la garde
  existante des liens s'applique.

PREREQUIS
  data/uk_sponsors.csv — telecharge par scripts/maj_registre_uk_v1.py
  (a rafraichir chaque mois). Sans lui, la source se declare indisponible
  avec un message clair.

Dependances : requests uniquement. Cles Adzuna lues dans l'environnement
ou .env (ADZUNA_APP_ID / ADZUNA_APP_KEY).
"""

from __future__ import annotations

import csv
import hashlib
import logging
import os
import re
from pathlib import Path

import urllib.parse as _up

import requests

from .base import Offre, SourceOffres
from .registre import enregistrer

log = logging.getLogger("yorbity.sources.uk")

RACINE = Path(__file__).resolve().parents[3]
CSV_REGISTRE = RACINE / "data" / "uk_sponsors.csv"
LIEN_REGISTRE = ("https://www.gov.uk/government/publications/"
                 "register-of-licensed-sponsors-workers")

REQUETES_METIER = ["electrician", "welder", "plumber", "carpenter",
                   "mechanic", "chef", "care worker", "bricklayer"]

# Suffixes juridiques a neutraliser pour apparier les noms d'employeurs.
_SUFFIXES = re.compile(
    r"\b(ltd|limited|plc|llp|llc|inc|group|holdings|uk|\(uk\)|co|company|"
    r"services|solutions|international)\b\.?", re.I)
_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")

BANDEAU = ("🛂 Employeur au registre officiel des sponsors (Home Office) : "
           "habilité à recruter des candidats internationaux. La décision "
           "de sponsoriser reste la sienne ; visa Skilled Worker soumis à "
           "conditions (salaire ≥ ~25 000 £).\n\n")


def _normaliser(nom: str) -> str:
    n = _NON_ALNUM.sub(" ", (nom or "").lower())
    n = _SUFFIXES.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()


def _cles_adzuna():
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_APP_KEY", "")
    if app_id and app_key:
        return app_id, app_key
    for env in (RACINE / ".env", RACINE / "app" / ".env"):
        if env.exists():
            for l in env.read_text(encoding="utf-8",
                                   errors="ignore").splitlines():
                if l.startswith("ADZUNA_APP_ID"):
                    app_id = l.split("=", 1)[1].strip().strip("'\"")
                if l.startswith("ADZUNA_APP_KEY"):
                    app_key = l.split("=", 1)[1].strip().strip("'\"")
    return app_id, app_key


class RegistreSponsors:
    """Le CSV du Home Office, indexe par nom normalise (charge une fois)."""

    def __init__(self):
        self._noms: set[str] | None = None

    def _charger(self) -> None:
        self._noms = set()
        if not CSV_REGISTRE.exists():
            log.warning("registre sponsors absent : %s — lance "
                        "scripts/maj_registre_uk_v1.py", CSV_REGISTRE)
            return
        with CSV_REGISTRE.open(encoding="utf-8", errors="ignore",
                               newline="") as f:
            lecteur = csv.reader(f)
            entete = next(lecteur, [])
            try:
                i = next(k for k, c in enumerate(entete)
                         if "organisation" in c.lower())
            except StopIteration:
                log.error("colonne Organisation introuvable : %s", entete)
                return
            for ligne in lecteur:
                if len(ligne) > i and ligne[i].strip():
                    self._noms.add(_normaliser(ligne[i]))
        log.info("registre sponsors UK : %s employeurs charges",
                 len(self._noms))

    def pret(self) -> bool:
        if self._noms is None:
            self._charger()
        return bool(self._noms)

    def est_sponsor(self, employeur: str) -> bool:
        if self._noms is None:
            self._charger()
        n = _normaliser(employeur)
        return bool(n) and n in self._noms


REGISTRE_HO = RegistreSponsors()


class UkSponsors(SourceOffres):
    nom = "uk_sponsors"
    libelle = "Royaume-Uni — Adzuna ∩ registre des sponsors (Home Office)"
    destinations = ("GB",)
    types_projet = ("emploi", "metier")

    PLAFOND = 500          # 10 pages Adzuna : balaye le job board (patch_fixpack2)

    def disponible(self) -> bool:
        ok_cles = all(_cles_adzuna())
        if not ok_cles:
            log.warning("uk_sponsors : cles Adzuna absentes")
        return ok_cles and REGISTRE_HO.pret()

    def admissible_sans_permis(self, destination, type_projet) -> bool:
        """True CONDITIONNEL : employeur licencie sponsor — le bandeau de
        chaque offre enonce la condition. C'est le seul sous-ensemble
        britannique adosse a une liste OFFICIELLE."""
        return True

    def lien_accessible_depuis_etranger(self, destination, type_projet) -> bool:
        return True   # liens Find a Job (gov.uk) : accessibles du monde entier
                      # (le lien Adzuna direct etait geo-bloque — patch_uk_lien)

    def lien_public(self, destination, type_projet) -> str:
        return LIEN_REGISTRE

    def lien_est_vivant(self, url: str) -> bool:
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            return r.status_code < 400
        except requests.RequestException:
            return False

    # ------------------------------------------------------------------ #
    def _adzuna_gb(self, mots_cles, limite):
        app_id, app_key = _cles_adzuna()
        offres = []
        pages = range(1, (limite // 50) + 2)  # patch_fixpack2
        for page in pages:
            if len(offres) >= limite:
                break
            try:
                r = requests.get(
                    f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}",
                    params={"app_id": app_id, "app_key": app_key,
                            "results_per_page": 50,
                            "what": mots_cles or REQUETES_METIER[0]},
                    timeout=20)
                r.raise_for_status()
                offres.extend(r.json().get("results", []))
            except Exception as e:
                log.error("Adzuna gb page %s : %s", page, e)
                break
        return offres[:limite]

    def collecter_page(self, destination, type_projet, mots_cles=None,
                       page=1, par_page=8, lang="en"):
        if not self.couvre(destination, type_projet):
            return [], 0
        if not REGISTRE_HO.pret():
            return [], 0
        brutes = self._adzuna_gb(mots_cles, self.PLAFOND)
        filtrees = [a for a in brutes
                    if REGISTRE_HO.est_sponsor(
                        (a.get("company") or {}).get("display_name", ""))]
        # Dedoublonnage titre+employeur (patch_fixpack) : Adzuna renvoie
        # souvent la meme annonce plusieurs fois.
        _vues, _dedup = set(), []
        for a in filtrees:
            k = ((a.get("title") or "").strip().lower(),
                 ((a.get("company") or {}).get("display_name") or "").lower())
            if k not in _vues:
                _vues.add(k)
                _dedup.append(a)
        filtrees = _dedup
        log.info("uk_sponsors : %s/%s offres chez des sponsors (was=%r)",
                 len(filtrees), len(brutes), mots_cles)
        total = len(filtrees)
        debut = (max(1, page) - 1) * par_page
        tranche = filtrees[debut:debut + par_page]
        return [self._vers_offre(a, type_projet) for a in tranche], total

    def collecter(self, destination, type_projet, mots_cles=None,
                  limite=8, lang="en"):
        offres, _ = self.collecter_page(destination, type_projet,
                                        mots_cles, 1, limite, lang)
        return offres

    def _vers_offre(self, a: dict, type_projet: str) -> Offre:
        # Le lien Adzuna direct (click.appcast.io) est geo-bloque hors UK
        # (« This job is not available in your area », constate 2026-07-10).
        # -> recherche titre+employeur sur le portail officiel Find a Job,
        # accessible partout (meme parade que l'Allemagne).
        _entreprise = (a.get("company") or {}).get("display_name", "")
        url = ("https://findajob.dwp.gov.uk/search?q="
               + _up.quote_plus(f"{a.get('title', '')} {_entreprise}".strip()))
        entreprise = (a.get("company") or {}).get("display_name", "")
        lieu = (a.get("location") or {}).get("display_name", "")
        desc = (a.get("description") or "")[:3500]
        sal = ""
        if a.get("salary_min"):
            sal = f"£{int(a['salary_min']):,}".replace(",", " ")
            if a.get("salary_max"):
                sal += f" – £{int(a['salary_max']):,}".replace(",", " ")
        return Offre(
            id=hashlib.sha1((str(a.get("id")) or url).encode()).hexdigest()[:16],
            titre=a.get("title", ""),
            url=url,
            source=self.nom,
            destination="GB",
            type_projet=type_projet,
            langue_source="en",
            entreprise=entreprise,
            lieu=lieu,
            salaire=sal,
            extrait=BANDEAU + desc,
            date=(a.get("created") or "")[:10],
            reference=f"UKS-{a.get('id', '')}",
            sans_permis=True,
        )


enregistrer(UkSponsors())
