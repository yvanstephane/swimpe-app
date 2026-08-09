"""
sources/adzuna.py — Adaptateur Adzuna, sous le contrat SourceOffres.

Ne reecrit rien : delegue a jobs_api._chercher_adzuna(), qui garde le cache
SQLite 12 h, le filtre BRUIT et la construction des mots-cles (_mots()).
L'import de jobs_api est PARESSEUX : jobs_api importe le registre, qui importe
ce module. Un import au niveau du fichier creerait un cycle.

admissible_sans_permis() = False partout.
Adzuna agrege des annonces d'employeurs ; rien dans sa reponse n'indique si
l'employeur accepte un candidat sans permis de travail. Repondre True serait
une promesse non verifiee. Seul Job Bank expose ce champ (fglo=1).
"""

from __future__ import annotations

import logging

from .base import Offre, SourceOffres
from .registre import enregistrer

log = logging.getLogger("yorbity.sources.adzuna")

# Repris de jobs_api.PAYS_ADZUNA
# GB retire (patch_uk_exclusif) : le Royaume-Uni est servi EXCLUSIVEMENT
# par uk_sponsors (registre Home Office + liens Find a Job accessibles
# partout). L'Adzuna generique n'y ajoutait que des doublons aux liens
# click.appcast.io geo-bloques.
DESTINATIONS = ("FR", "CA", "DE", "US", "IT", "ES", "NL", "AT", "BE",
                "CH", "AU", "NZ", "BR", "IN", "MX", "PL", "SG", "ZA")

ANGLOPHONES = {"GB", "US", "AU", "NZ", "IN", "SG", "ZA", "CA"}


class Adzuna(SourceOffres):
    nom = "adzuna"
    libelle = "Adzuna — agregateur d'offres"
    destinations = DESTINATIONS
    types_projet = ("stage", "emploi", "metier")

    # ----------------------------------------------------------------------- #
    def _api(self):
        """Import paresseux : evite le cycle jobs_api <-> registre."""
        import jobs_api
        return jobs_api

    def disponible(self) -> bool:
        try:
            return self._api().disponible()
        except Exception as e:
            log.warning("Adzuna indisponible : %s", e)
            return False

    def admissible_sans_permis(self, destination: str, type_projet: str) -> bool:
        """
        Adzuna n'expose aucun champ "ouvert aux candidats internationaux".
        On ne repond pas True sans preuve.
        """
        return False

    def lien_accessible_depuis_etranger(self, destination: str, type_projet: str) -> bool:
        """
        Prouve par scripts/diag_geoblocage.py (2026-07-10) : adzuna.ca depuis
        la France -> SUBSTITUE x3 ("Sorry, this job is not available in your
        region"). Chaque domaine national ne sert que ses visiteurs locaux.
        Un utilisateur a Douala, Lima ou Hanoi verra le meme mur sur TOUS les
        domaines Adzuna. Les metadonnees API, elles, passent partout : la
        carte s'affiche, seul le lien est masque.
        """
        return False

    def lien_public(self, destination: str, type_projet: str) -> str:
        return f"https://www.adzuna.com/search?loc={destination.lower()}"

    # ----------------------------------------------------------------------- #
    def collecter(
        self,
        destination: str,
        type_projet: str,
        mots_cles: str | None = None,
        limite: int = 8,
        lang: str = "fr",
    ) -> list[Offre]:
        if not self.couvre(destination, type_projet):
            return []

        try:
            api = self._api()
        except Exception as e:
            log.error("jobs_api introuvable : %s", e)
            return []

        fn = getattr(api, "_chercher_adzuna", None) or getattr(api, "chercher", None)
        if fn is None:
            log.error("jobs_api n'expose ni _chercher_adzuna ni chercher")
            return []

        try:
            brut = fn(destination, type_projet, mots_cles or "")
        except Exception as e:
            log.error("Adzuna en erreur : %s", e)
            return []

        dest = destination.upper()
        langue_source = "en" if dest in ANGLOPHONES else "fr"

        offres = []
        for o in brut[:limite]:
            if not o.get("url"):
                continue
            offres.append(Offre(
                id=str(o.get("id", "")),
                titre=o.get("titre", ""),
                url=o.get("url", ""),
                source=self.nom,
                destination=dest,
                type_projet=type_projet,
                langue_source=langue_source,
                entreprise=o.get("entreprise", ""),
                lieu=o.get("lieu", ""),
                salaire=o.get("salaire", ""),
                extrait=o.get("extrait", ""),
                date=o.get("date", ""),
                # Adzuna n'a pas de reference employeur : on garde l'ancien repli.
                reference=f"JOB-{str(o.get('id', ''))[:10]}",
                sans_permis=False,
                domaine=mots_cles or "",
            ))
        log.info("Adzuna %s/%s : %s offres.", dest, type_projet, len(offres))
        return offres


enregistrer(Adzuna())
