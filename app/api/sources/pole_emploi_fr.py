"""
sources/_modele.py — Copier ce fichier pour ajouter une source.

    cp app/api/sources/_modele.py app/api/sources/pole_emploi_fr.py

Puis : remplir les 4 attributs, implementer collecter() et lien_public(),
et ajouter `from . import pole_emploi_fr` dans registre.charger_defaut().

Ce fichier n'est PAS enregistre (pas d'appel a enregistrer() en bas).
"""

from __future__ import annotations

import hashlib
import logging

from .base import Offre, SourceOffres

log = logging.getLogger("yorbity.sources.modele")


class MaSource(SourceOffres):
    nom = "ma_source"                       # identifiant technique, sans espace
    libelle = "Nom affiche a l'admin"
    destinations = ("FR",)                  # codes ISO-2 majuscules
    types_projet = ("stage", "emploi")      # parmi etudes/stage/emploi/metier

    # ----------------------------------------------------------------------- #
    def disponible(self) -> bool:
        """Ex : verifier que la cle API est dans .env."""
        # import os; return bool(os.getenv("MA_SOURCE_API_KEY"))
        return True

    def admissible_sans_permis(self, destination: str, type_projet: str) -> bool:
        """
        LA question a se poser pour chaque pays :
        un candidat encore a l'etranger, SANS titre de sejour ni permis de
        travail, peut-il postuler a ce type d'offre ?

        Au Canada la reponse est non pour les emplois etudiants (prouve : le
        filtre Summer Jobs croise avec 'international candidates' rend 0 offre).
        Ne reponds True que si tu l'as verifie.
        """
        return False

    def lien_public(self, destination: str, type_projet: str) -> str:
        """
        URL montree a l'utilisateur.
        ATTENTION : verifier qu'elle ne geo-bloque pas et n'affiche pas de
        popup du type "vous consultez ce site depuis l'etranger".
        """
        return "https://exemple.fr/offres"

    def lien_est_vivant(self, url: str) -> bool:
        return True

    # ----------------------------------------------------------------------- #
    def collecter(
        self,
        destination: str,
        type_projet: str,
        mots_cles: str | None = None,
        limite: int = 50,
        lang: str = "fr",
    ) -> list[Offre]:
        if not self.couvre(destination, type_projet):
            return []

        offres: list[Offre] = []
        # for brut in appel_api(...):
        #     offres.append(Offre(
        #         id=hashlib.sha1(brut["url"].encode()).hexdigest()[:16],
        #         titre=brut["intitule"],
        #         url=brut["url"],
        #         source=self.nom,
        #         destination=destination.upper(),
        #         type_projet=type_projet,
        #         langue_source=lang,
        #         entreprise=brut.get("entreprise", ""),
        #         lieu=brut.get("lieu", ""),
        #         salaire=brut.get("salaire", ""),
        #         extrait=brut.get("description", "")[:4000],
        #         date=brut.get("date", ""),          # ISO : 2026-07-09
        #         reference=brut.get("reference", ""), # celle de l'EMPLOYEUR
        #         sans_permis=self.admissible_sans_permis(destination, type_projet),
        #     ))
        return offres


# Decommenter une fois la source prete :
# from .registre import enregistrer
# enregistrer(MaSource())
