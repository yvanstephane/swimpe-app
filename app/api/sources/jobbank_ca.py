"""
sources/jobbank_ca.py — Adaptateur Job Bank (Canada).

FAITS ETABLIS PAR scripts/sonde_jobbank.py — ne pas re-deviner :

  * Flux Atom : /jobsearch/feed/jobSearchRSSfeed
  * Mot-cle   : `dkw` (seul parametre qui filtre reellement).
                `jkw`, `q`, `term`, `keyword` sont IGNORES : ils rendent
                exactement le flux par defaut.
                `dkw` cherche en PLEIN TEXTE. Le bloc d'inclusion standard de
                Job Bank contient "Are you currently a student?" -> presque
                toutes les annonces matchent "student". Ne jamais scorer sur ce
                mot seul.
  * fglo=1    : "Canadians AND international candidates". Le seul sous-ensemble
                postulable SANS permis de travail.
  * fsrc=21   : Summer Jobs.       fsrc=21 + fglo=1  ->  0 offre.
  * fsrc=16   : Canada Summer Jobs.
  * fsrc=32   : Temporary Foreign Workers.
  * fexp=0    : aucune experience requise. fexp=0 + fglo=1 -> 58 offres.

CONSEQUENCE PRODUIT :
  Au Canada, il n'existe AUCUN emploi etudiant ouvert a un candidat sans
  permis. Le travail hors campus 20 h/semaine exige un permis d'etudes valide.
  -> admissible_sans_permis("CA", "stage"|"emploi") = False
  -> admissible_sans_permis("CA", "metier")         = True   (fglo=1)

  La carte affichee doit donc s'appeler "Emplois ouverts aux candidats
  internationaux", pas "Emploi etudiant au Canada".

Detail d'une offre : RDFa (property="..."), pas de JSON-LD.
  employeur   [property="hiringOrganization"]
  lieu        [property="addressLocality"] + [property="addressRegion"]
  description [property="description"]
  date        [property="datePosted"]   -> "Posted on July 09, 2026"
  salaire     [property="baseSalary"]
  reference   aucun "Job number" dans la page -> id d'URL /jobposting/49871578
Pieges : span[property="name"] attrape "Government of Canada" ;
         <time> porte une date sans rapport avec la publication.
"""

from __future__ import annotations

import re
import time
import hashlib
import logging
from datetime import datetime
from urllib.parse import urljoin, urlencode
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .base import Offre, SourceOffres
from .registre import enregistrer

log = logging.getLogger("yorbity.sources.jobbank_ca")

BASE = "https://www.jobbank.gc.ca"
FEED = f"{BASE}/jobsearch/feed/jobSearchRSSfeed"
SEARCH = f"{BASE}/jobsearch/jobsearch"
ATOM = "{http://www.w3.org/2005/Atom}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9,fr-CA;q=0.8",
}

BRUIT = re.compile(
    r"\b(uber|uber\s*eats|deliveroo|lyft|doordash|skip\s*the\s*dishes|"
    r"instacart|vtc|amazon\s*flex|courier\s*partner)\b",
    re.I,
)

# Le boilerplate Job Bank contient "Are you currently a student?".
# On ne compte donc les mots-cles QUE dans le titre.
MOTS_TITRE = re.compile(
    r"\b(student|intern|internship|apprentice|co-?op|trainee|junior|summer)s?\b", re.I
)

_MOIS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _propre_url(href: str) -> str:
    return urljoin(BASE, href.split(";jsessionid")[0].split("?source=")[0])


def _reference(url: str) -> str:
    m = re.search(r"/jobposting/(\d+)", url)
    return f"JOB-{m.group(1)}" if m else ""


def _txt(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _date_iso(brut: str) -> str:
    if not brut:
        return ""
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", brut)
    if m and (mois := _MOIS.get(m.group(1).lower())):
        try:
            return datetime(int(m.group(3)), mois, int(m.group(2))).strftime("%Y-%m-%d")
        except ValueError:
            pass
    m = re.search(r"\d{4}-\d{2}-\d{2}", brut)
    return m.group(0) if m else ""


class JobBankCanada(SourceOffres):
    nom = "jobbank_ca"
    libelle = "Job Bank Canada — candidats internationaux"
    destinations = ("CA",)
    types_projet = ("stage", "emploi", "metier")

    delai = 1.2  # politesse : site gouvernemental

    # ----------------------------------------------------------------------- #
    def admissible_sans_permis(self, destination: str, type_projet: str) -> bool:
        """
        Prouve par la sonde : fsrc=21 (Summer Jobs) + fglo=1 -> 0 offre.
        Seuls les postes fglo=1 (recrutement international) sont accessibles
        a quelqu'un qui n'a pas encore de permis. Ce ne sont pas des emplois
        etudiants : ce sont des postes permanents avec permis de travail.
        """
        return destination.upper() == "CA" and type_projet == "metier"

    def lien_public(self, destination: str, type_projet: str) -> str:
        if self.admissible_sans_permis(destination, type_projet):
            # fglo=1 : pas de popup "you are visiting from outside Canada"
            return f"{SEARCH}?fglo=1&sort=M"
        return f"{BASE}/findajob/foreign-candidates"

    def lien_est_vivant(self, url: str) -> bool:
        try:
            r = _session().head(url, timeout=10, allow_redirects=True)
            if r.status_code == 405:
                r = _session().get(url, timeout=10, stream=True)
            return r.status_code < 400
        except requests.RequestException:
            return False

    def lien_accessible_depuis_etranger(self, destination: str, type_projet: str) -> bool:
        """
        Prouve par scripts/diag_geoblocage.py (2026-07-10) : contenu RDFa
        complet servi depuis la France, simple banniere informative (AVERTI).
        C'est la raison d'etre de fglo=1 : etre vu de l'etranger.
        """
        return True

    # ----------------------------------------------------------------------- #
    def _params(self, type_projet: str, mots_cles: str | None, limite: int, lang: str) -> dict:
        # L'UI envoie parfois le domaine brut ("Tous secteurs", "Tous les
        # domaines", "All sectors"...). dkw cherche en plein texte : un
        # generique ne filtre rien d'utile. On neutralise, comme _mots()
        # d'Adzuna. (Vu en production : "Tous les domaines".)
        if mots_cles and re.fullmatch(
            r"\s*(tous(\s+les)?\s+(secteurs?|domaines?|postes?)"
            r"|all(\s+(sectors?|domains?|jobs?))?"
            r"|tous|toutes)\s*",
            mots_cles, re.I,
        ):
            mots_cles = None
        p = {"sort": "D", "rows": limite, "lang": lang}
        if self.admissible_sans_permis("CA", type_projet):
            p["fglo"] = 1
        if type_projet in ("stage", "emploi"):
            p["fsrc"] = 21          # Summer Jobs
        if mots_cles:
            p["dkw"] = mots_cles    # le seul qui filtre
        return p

    def _liste(self, params: dict, timeout: int) -> list[dict]:
        r = _session().get(f"{FEED}?{urlencode(params)}", timeout=timeout)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        out = []
        for e in root.findall(ATOM + "entry"):
            lien = e.find(ATOM + "link")
            href = lien.get("href") if lien is not None else None
            if not href:
                continue
            t = e.find(ATOM + "title")
            s = e.find(ATOM + "summary")
            out.append({
                "url": _propre_url(href),
                "titre": (t.text or "").strip() if t is not None else "",
                "resume": (s.text or "").strip() if s is not None else "",
            })
        return out

    def _detail(self, url: str, s: requests.Session, timeout: int) -> dict:
        vide = {"entreprise": "", "lieu": "", "extrait": "", "salaire": "", "date": ""}
        try:
            r = s.get(url, timeout=timeout)
            r.raise_for_status()
        except requests.RequestException as e:
            log.warning("detail KO %s : %s", url, e)
            return vide

        soup = BeautifulSoup(r.text, "html.parser")
        # PAS span[property="name"] : il attrape "Government of Canada".
        entreprise = _txt(soup.select_one('[property="hiringOrganization"]'))

        ville = _txt(soup.select_one('[property="addressLocality"]'))
        region = _txt(soup.select_one('[property="addressRegion"]'))
        lieu = f"{ville} ({region})" if ville and region else (ville or region)

        desc = _txt(soup.select_one('[property="description"]'))
        if not desc:
            desc = _txt(soup.select_one("div.job-posting-detail-requirements"))
        desc = re.sub(r"\s{3,}", "\n\n", desc)[:4000]

        salaire = re.sub(r"\s+", " ", _txt(soup.select_one('[property="baseSalary"]')))
        salaire = salaire.replace("$ ", "$")

        dp = soup.select_one('[property="datePosted"]')
        date = _date_iso(dp.get("content") or _txt(dp)) if dp else ""

        return {"entreprise": entreprise, "lieu": lieu, "extrait": desc,
                "salaire": salaire, "date": date}

    # ----------------------------------------------------------------------- #
    def collecter(
        self,
        destination: str,
        type_projet: str,
        mots_cles: str | None = None,
        limite: int = 50,
        lang: str = "en",
    ) -> list[Offre]:
        if not self.couvre(destination, type_projet):
            return []

        sans_permis = self.admissible_sans_permis(destination, type_projet)
        params = self._params(type_projet, mots_cles, limite, lang)

        try:
            brut = self._liste(params, timeout=25)
        except Exception as e:
            log.error("Flux Atom Job Bank indisponible : %s", e)
            return []

        if not brut:
            log.info("Job Bank : 0 resultat pour %s (params=%s)", type_projet, params)
            return []

        s = _session()
        offres, vus = [], set()
        for c in brut:
            # PLAFOND CLIENT — indispensable. Prouve par diag_registre
            # (2026-07-10) : le flux IGNORE `rows` et renvoie ~100 entrees.
            # Sans ce plafond, on ouvre 100 pages de detail a 1,2 s
            # d'intervalle = 2 a 4 minutes de chargement silencieux.
            # C'etait la vraie cause du "0 offre affichee" dans Streamlit.
            if len(offres) >= max(1, limite):
                break
            if c["url"] in vus or BRUIT.search(c["titre"]):
                continue
            vus.add(c["url"])

            time.sleep(self.delai)
            d = self._detail(c["url"], s, timeout=25)
            if BRUIT.search(d["entreprise"]):
                continue

            offres.append(Offre(
                id=hashlib.sha1(c["url"].encode()).hexdigest()[:16],
                titre=c["titre"],
                url=c["url"],
                source=self.nom,
                destination="CA",
                type_projet=type_projet,
                langue_source="fr" if lang == "fr" else "en",
                entreprise=d["entreprise"],
                lieu=d["lieu"],
                salaire=d["salaire"],
                extrait=d["extrait"] or c["resume"],
                date=d["date"],
                reference=_reference(c["url"]),
                sans_permis=sans_permis,
                score=len(set(m.lower() for m in MOTS_TITRE.findall(c["titre"]))),
            ))

        offres.sort(key=lambda o: (-o.score, o.date), reverse=False)
        log.info("Job Bank %s : %s offres.", type_projet, len(offres))
        return offres


    def collecter_page(
        self,
        destination: str,
        type_projet: str,
        mots_cles: str | None = None,
        page: int = 1,
        par_page: int = 8,
        lang: str = "en",
    ) -> tuple[list[Offre], int]:
        """
        Pagination a cout CONSTANT.

        Le flux Atom rend ~100 entrees pour UNE requete (titre + URL).
        Le detail RDFa coute UNE requete HTTP par offre, a 1,2 s de politesse.
        On enrichit donc uniquement les `par_page` offres de la page demandee :
        page 1 ou page 12, le cout est le meme (~10 s), et l'utilisateur peut
        parcourir les 100 offres au lieu des 8 premieres.
        """
        if not self.couvre(destination, type_projet):
            return [], 0

        page = max(1, page)
        params = self._params(type_projet, mots_cles, 100, lang)
        try:
            brut = self._liste(params, timeout=25)
        except Exception as e:
            log.error("Flux Atom Job Bank indisponible : %s", e)
            return [], 0

        # Dedup + anti-bruit sur le titre : gratuit, avant tout appel reseau.
        vus, propres = set(), []
        for c in brut:
            if c["url"] in vus or BRUIT.search(c["titre"]):
                continue
            vus.add(c["url"])
            propres.append(c)

        total = len(propres)
        debut = (page - 1) * par_page
        tranche = propres[debut:debut + par_page]
        if not tranche:
            return [], total

        sans_permis = self.admissible_sans_permis(destination, type_projet)
        s = _session()
        offres = []
        for c in tranche:
            time.sleep(self.delai)
            d = self._detail(c["url"], s, timeout=25)
            if BRUIT.search(d["entreprise"]):
                continue
            offres.append(Offre(
                id=hashlib.sha1(c["url"].encode()).hexdigest()[:16],
                titre=c["titre"],
                url=c["url"],
                source=self.nom,
                destination="CA",
                type_projet=type_projet,
                langue_source="fr" if lang == "fr" else "en",
                entreprise=d["entreprise"],
                lieu=d["lieu"],
                salaire=d["salaire"],
                extrait=d["extrait"] or c["resume"],
                date=d["date"],
                reference=_reference(c["url"]),
                sans_permis=sans_permis,
                score=len(set(m.lower() for m in MOTS_TITRE.findall(c["titre"]))),
            ))
        log.info("Job Bank page %s : %s/%s offres.", page, len(offres), total)
        return offres, total


enregistrer(JobBankCanada())
