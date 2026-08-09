# =============================================================================
# destinations_monde.py — Ouvre TOUS les pays du monde comme destinations
# Les 36 fiches détaillées existantes restent intactes ; les autres pays
# reçoivent une fiche GÉNÉRALE (admission directe + visa + accompagnement),
# activable/désactivable en admin comme les autres.
# =============================================================================
from pays_monde import ORIGINES_MONDE

def _drapeau(code):
    """Drapeau emoji à partir du code ISO-2."""
    try:
        return chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))
    except Exception:
        return "🌍"

def completer_destinations(D):
    """Ajoute une fiche générale pour chaque pays absent de D."""
    codes_existants = set(D.keys())
    noms_existants = {v["nom"] for v in D.values()}
    for nom, (code, _devise) in ORIGINES_MONDE.items():
        if code in codes_existants or nom in noms_existants:
            continue
        D[code] = dict(
            nom=nom,
            flag=_drapeau(code),
            resume=(f"{nom} accueille des étudiants internationaux dans ses universités "
                    f"et écoles. Fiche générale : les conditions exactes varient selon "
                    f"l'établissement et ta nationalité — notre équipe peut monter le "
                    f"parcours précis pour toi."),
            ressources="Variable selon l'établissement et le type de visa — à vérifier auprès des sources officielles",
            travail="Selon la législation locale sur les étudiants étrangers",
            post="Selon le titre de séjour obtenu",
            portail=None,
            services=["ORIENT", "ADMIS", "DOSSIER", "VISA", "TRAD"],
            etapes=[
                ("Identifier les établissements qui recrutent à l'international",
                 "Universités publiques, écoles privées reconnues, programmes en anglais "
                 "ou dans la langue locale : on t'aide à cibler ceux qui correspondent à "
                 "ton profil et ton budget.", None, "ORIENT"),
                ("Candidater directement auprès de l'établissement",
                 "Dossier académique, traductions certifiées des diplômes, lettre de "
                 "motivation : la candidature se fait en direct — exactement le type de "
                 "démarche que nous prenons en charge.", None, "ADMIS"),
                ("Obtenir le visa étudiant",
                 "Lettre d'admission + preuve de ressources + assurance : la liste exacte "
                 "dépend de ta nationalité et du consulat compétent.", None, "VISA"),
            ],
            bourses=[
                ("Bourses locales et accords bilatéraux",
                 "La plupart des pays offrent des bourses via leurs universités ou des "
                 "accords avec ton gouvernement — nous pouvons faire la recherche ciblée "
                 "pour ton profil.", None),
            ],
        )
    return D
