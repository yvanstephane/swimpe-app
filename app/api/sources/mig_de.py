"""
sources/mig_de.py — Allemagne, via l'API publique du job board federal.

GISEMENT
  Les offres de make-it-in-germany.com proviennent du job board de la
  Bundesagentur fur Arbeit (BA). La BA expose une API REST publique,
  documentee par la communaute (bund.dev) :
      GET https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs
      En-tete : X-API-Key: jobboerse-jobsuche          (cle publique)
      Params  : was=<metier>  wo=<ville>  page=<n>  size=<n>
  Detail :
      GET .../pc/v2/jobdetails/<base64url(refnr)>
  -> PAGINATION NATIVE : contrairement a Job Bank, pas besoin d'ouvrir une
     page HTML par offre pour la liste ; le detail ne sert qu'a la
     description complete.

HONNETETE (lecon du Canada, fglo=1)
  Make it in Germany n'affiche QUE les employeurs ayant coche l'opt-in
  "publication internationale". Le parametre API correspondant n'est PAS
  encore identifie : tant que scripts/sonde_mig.py ne l'a pas confirme,
  cet adaptateur interroge le job board ENTIER et déclare donc
      admissible_sans_permis = False
  On n'affirme pas qu'un employeur recrute a l'international sans preuve.
  Des que la sonde revele le drapeau, on l'ajoute a _params() et on passe
  metier -> True.

Dependances : requests uniquement.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import re

import urllib.parse as _up

import requests

from .base import Offre, SourceOffres
from .registre import enregistrer

log = logging.getLogger("yorbity.sources.mig_de")

API = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
CLE_PUBLIQUE = "jobboerse-jobsuche"

LIEN_MIG = ("https://www.make-it-in-germany.com/en/working-in-germany/"
            "job-listings")

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0 Safari/537.36"),
    "X-API-Key": CLE_PUBLIQUE,
    "Accept": "application/json",
}

# Le moteur BA est optimise pour l'ALLEMAND : on traduit les requetes
# generiques ; un metier precis passe tel quel (souvent identique : Elektriker).
REQUETES_METIER_DE = ["Elektriker", "Schweisser", "Mechatroniker",
                      "Anlagenmechaniker", "Pflegefachkraft", "Koch"]

BRUIT = re.compile(r"\b(zeitarbeit|leiharbeit|uber|lieferando)\b", re.I)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _refnr_b64(refnr: str) -> str:
    return base64.urlsafe_b64encode(refnr.encode()).decode().rstrip("=")


def _nettoyer(txt: str, maxi: int = 4000) -> str:
    txt = re.sub(r"<[^>]+>", " ", txt or "")
    txt = re.sub(r"[ \t]{2,}", " ", txt)
    txt = re.sub(r"\s{3,}", "\n\n", txt).strip()
    return txt[:maxi]


class MakeItInGermany(SourceOffres):
    nom = "mig_de"
    libelle = "Allemagne — job board fédéral (Make it in Germany / BA)"
    destinations = ("DE",)
    types_projet = ("emploi", "metier")

    # ------------------------------------------------------------------ #
    def admissible_sans_permis(self, destination: str, type_projet: str) -> bool:
        """False TANT QUE la sonde n'a pas identifie le drapeau opt-in MIG.
        Voir scripts/sonde_mig.py. On ne repete pas l'erreur du Canada :
        aucune promesse sans parametre prouve."""
        return False

    def lien_accessible_depuis_etranger(self, destination: str, type_projet: str) -> bool:
        """arbeitsagentur.de et make-it-in-germany.com ne geo-bloquent pas
        (portails concus pour les candidats etrangers). A confirmer par
        diag_geoblocage si un doute apparait."""
        return True

    def lien_public(self, destination: str, type_projet: str) -> str:
        return LIEN_MIG

    def lien_est_vivant(self, url: str) -> bool:
        try:
            r = _session().head(url, timeout=10, allow_redirects=True)
            if r.status_code == 405:
                r = _session().get(url, timeout=10, stream=True)
            return r.status_code < 400
        except requests.RequestException:
            return False

    # ------------------------------------------------------------------ #
    def _params(self, mots_cles: str | None, page: int, size: int) -> dict:
        p = {"page": max(1, page), "size": max(1, min(size, 25)),
             "angebotsart": 1}          # 1 = emploi (pas formation/interim)
        if mots_cles:
            p["was"] = mots_cles
        # TODO (sonde_mig) : ajouter ici le drapeau opt-in international MIG
        return p

    # Routes candidates pour le detail : la BA a retire pc/v2/jobdetails
    # (403 "No match found", sonde du 2026-07-10). On essaie une matrice et
    # on memorise la premiere qui repond — auto-adaptatif si la BA rechange.
    _DETAIL_ROUTES = [
        API + "/pc/v4/jobdetails/{b64}",
        API + "/pc/v2/jobdetails/{b64}",
        API + "/pc/v2/jobdetails/{b64pad}",
        API + "/pc/v1/jobdetails/{b64}",
        API + "/pc/v4/app/jobs/{refnr}",
    ]
    _route_ok: int | None = None

    def _detail(self, refnr: str, s: requests.Session, timeout: int) -> str:
        if not refnr:
            return ""
        b64 = _refnr_b64(refnr)
        b64pad = base64.urlsafe_b64encode(refnr.encode()).decode()
        routes = self._DETAIL_ROUTES
        ordre = ([self._route_ok] if self._route_ok is not None else []) + [
            i for i in range(len(routes)) if i != self._route_ok]
        for i in ordre:
            url = routes[i].format(b64=b64, b64pad=b64pad, refnr=refnr)
            try:
                r = s.get(url, timeout=timeout)
                if r.status_code != 200:
                    continue
                j = r.json()
                desc = (j.get("stellenbeschreibung")
                        or j.get("stellenangebotsBeschreibung") or "")
                if desc:
                    if self._route_ok != i:
                        type(self)._route_ok = i
                        log.info("detail BA : route %s retenue", routes[i])
                    return _nettoyer(desc)
            except Exception as e:
                log.debug("detail route %s KO : %s", i, e)
        return ""

    def _vers_offre(self, a: dict, type_projet: str, description: str) -> Offre:
        refnr = a.get("refnr", "")
        lieu_d = (a.get("arbeitsort") or {})
        lieu = ", ".join(x for x in [lieu_d.get("ort"),
                                     lieu_d.get("region")] if x)
        # jobdetail/{refnr} redirige vers l'accueil Jobsuche (constate
        # 2026-07-10). La BA indique que la Referenznummer est cherchable :
        # la recherche par reference atterrit sur le poste exact.
        url = (a.get("externeUrl")
               or "https://www.arbeitsagentur.de/jobsuche/suche?was="
               + _up.quote(refnr))
        return Offre(
            id=hashlib.sha1((refnr or url).encode()).hexdigest()[:16],
            titre=a.get("titel") or a.get("beruf", ""),
            url=url,
            source=self.nom,
            destination="DE",
            type_projet=type_projet,
            langue_source="de",
            entreprise=a.get("arbeitgeber", ""),
            lieu=lieu,
            salaire="",                        # la BA ne publie pas le salaire
            extrait=description,
            date=(a.get("aktuelleVeroeffentlichungsdatum") or "")[:10],
            reference=f"BA-{refnr}" if refnr else "",
            sans_permis=False,
        )

    # ------------------------------------------------------------------ #
    def collecter_page(self, destination, type_projet, mots_cles=None,
                       page=1, par_page=8, lang="de"):
        """Pagination NATIVE de l'API BA : 1 requete liste + N details."""
        if not self.couvre(destination, type_projet):
            return [], 0
        s = _session()
        try:
            r = s.get(f"{API}/pc/v4/jobs",
                      params=self._params(mots_cles, page, par_page),
                      timeout=20)
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            log.error("API BA indisponible : %s", e)
            return [], 0

        total = int(j.get("maxErgebnisse") or 0)
        offres = []
        for a in j.get("stellenangebote", []):
            titre = a.get("titel") or a.get("beruf", "")
            if BRUIT.search(titre) or BRUIT.search(a.get("arbeitgeber", "")):
                continue
            desc = self._detail(a.get("refnr", ""), s, timeout=15)
            offres.append(self._vers_offre(a, type_projet, desc))
        log.info("BA page %s : %s offres / %s total (was=%r)",
                 page, len(offres), total, mots_cles)
        return offres, total

    def collecter(self, destination, type_projet, mots_cles=None,
                  limite=8, lang="de"):
        offres, _ = self.collecter_page(destination, type_projet,
                                        mots_cles, page=1,
                                        par_page=limite, lang=lang)
        return offres


enregistrer(MakeItInGermany())
