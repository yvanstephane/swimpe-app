"""
sources/base.py — Le CONTRAT que toute source d'offres doit respecter.

Pourquoi : Yorbity vise 40+ destinations x 4 types de projet. Coder Job Bank
en dur (fglo, dkw, selecteurs RDFa) dans offres_sync ne passe pas a l'echelle.
Chaque source devient un adaptateur qui implemente ce contrat ; le registre
les assemble. Ajouter la France = ecrire pole_emploi.py + l'enregistrer.

Le dict renvoye par collecter() est celui que jobs_api.py consomme deja :
    {id, titre, entreprise, lieu, salaire, extrait, date, url}
Rien a changer cote affichage.

Champ decisif : admissible_sans_permis().
    Le Canada l'a demontre — les emplois etudiants existent, mais AUCUN n'est
    ouvert a un candidat sans permis (fsrc=21 + fglo=1 -> 0 offre).
    Cette contrainte est propre a chaque pays x type. Le contrat la porte,
    pour qu'aucune source ne promette a un candidat ce qu'il ne peut pas obtenir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone

# Les 4 types de projet Yorbity
TYPES_PROJET = ("etudes", "stage", "emploi", "metier")


@dataclass
class Offre:
    """Format pivot. Compatible avec jobs_api.py sans adaptation."""
    id: str
    titre: str
    url: str
    source: str                  # "jobbank_ca", "adzuna", ...
    destination: str             # code pays ISO-2 majuscule : "CA", "FR"
    type_projet: str             # un de TYPES_PROJET
    langue_source: str = "en"    # pour traduction_offres
    entreprise: str = ""
    lieu: str = ""
    salaire: str = ""
    extrait: str = ""            # description, tronquee
    date: str = ""               # ISO 8601 : "2026-07-09"
    reference: str = ""          # numero a recopier dans le formulaire
    sans_permis: bool = False    # postulable sans permis de travail ?
    domaine: str = ""
    score: int = 0
    ingere_le: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        return asdict(self)


class SourceOffres(ABC):
    """
    Un adaptateur par (site, pays). Sous-classer, puis enregistrer :

        from .registre import enregistrer
        enregistrer(MaSource())
    """

    # --- identite (a definir dans la sous-classe) --------------------------- #
    nom: str = ""                       # identifiant technique, ex "jobbank_ca"
    libelle: str = ""                   # affiche a l'admin
    destinations: tuple[str, ...] = ()  # ("CA",) ou ("FR", "BE")
    types_projet: tuple[str, ...] = ()  # sous-ensemble de TYPES_PROJET

    # --- contrat ------------------------------------------------------------ #
    @abstractmethod
    def collecter(
        self,
        destination: str,
        type_projet: str,
        mots_cles: str | None = None,
        limite: int = 50,
        lang: str = "en",
    ) -> list[Offre]:
        """Renvoie les offres. Doit deja etre dedupliquee et debruitee."""

    @abstractmethod
    def lien_public(self, destination: str, type_projet: str) -> str:
        """
        URL a montrer a l'utilisateur.
        Doit pointer vers une page qui NE le rejette PAS (pas de geo-blocage,
        pas de popup 'you are visiting from outside Canada').
        """

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
        Renvoie (offres de la page, total disponible).

        Implementation par defaut : collecte page*par_page offres et decoupe.
        Correcte, mais couteuse si la source facture chaque offre.

        A SURCHARGER quand la source separe le peu cher du cher :
          - Job Bank : la LISTE (flux Atom) est gratuite et rend ~100 entrees ;
            seul le DETAIL coute une requete HTTP par offre. On n'enrichit donc
            que le decoupage de la page -> cout constant, pagination illimitee.
          - Adzuna : pagination native /search/{page}, aucun surcout.
        """
        page = max(1, page)
        besoin = page * par_page
        tout = self.collecter(destination, type_projet, mots_cles, besoin, lang)
        debut = (page - 1) * par_page
        return tout[debut:debut + par_page], len(tout)

    def admissible_sans_permis(self, destination: str, type_projet: str) -> bool:
        """
        Ce (pays, type) offre-t-il des postes accessibles a quelqu'un qui n'a
        pas encore de permis de travail ? Defaut prudent : non.
        """
        return False

    def lien_accessible_depuis_etranger(self, destination: str, type_projet: str) -> bool:
        """
        Le lien de l'offre s'ouvre-t-il pour un visiteur HORS du pays de
        destination ?

        Etabli par scripts/diag_geoblocage.py (2026-07-10) :
          - Adzuna SUBSTITUE le contenu ("not available in your region")
            pour un visiteur hors du domaine national -> False.
          - Job Bank sert le contenu avec une simple banniere -> True.

        False n'exclut PAS la source : ses metadonnees (titre, salaire,
        description via API) restent affichables partout. Seul le lien est
        masque au visiteur ; l'admin le voit toujours.
        Defaut optimiste : True (la plupart des sites servent leurs pages).
        """
        return True

    def disponible(self) -> bool:
        """Cles API presentes, service joignable. Defaut : oui."""
        return True

    def couvre(self, destination: str, type_projet: str | None = None) -> bool:
        if destination.upper() not in self.destinations:
            return False
        if type_projet is not None and type_projet not in self.types_projet:
            return False
        return True

    def lien_est_vivant(self, url: str) -> bool:
        """Verification 404. Surcharger si la source a mieux."""
        return True

    def __repr__(self) -> str:
        return f"<{self.nom} {list(self.destinations)} {list(self.types_projet)}>"
