#!/usr/bin/env python3
# =============================================================================
# seed_demo.py — Crée la table `opportunites` + exemples réels sourcés
# pour que le dashboard fonctionne dès le premier lancement.
# Usage : python scripts/seed_demo.py
# =============================================================================
import sqlite3, datetime
DB = "data/mobilite.db"
TODAY = datetime.date.today().isoformat()

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunites(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT,              -- formation | bourse | emploi | stage
  titre TEXT,
  destination TEXT,       -- code ISO destination
  origines_eligibles TEXT,-- 'TOUS' ou liste de codes 'CM,GA,HT'
  niveau TEXT,            -- lycee/licence/master/doctorat/pro
  domaine TEXT,
  montant TEXT,
  deadline TEXT,          -- AAAA-MM-JJ si connue
  source_url TEXT,
  maj TEXT,
  statut TEXT DEFAULT 'a_verifier');
"""

DEMO = [
 ("bourse","Bourse MEXT (gouvernement du Japon) — licence/master/doctorat","JP","TOUS",
  "licence,master,doctorat","tous domaines","Scolarité complète + ~143-145 000 JPY/mois + billets",
  None,"https://www.studyinjapan.go.jp/fr/planning/scholarships/mext-scholarships/",TODAY),
 ("bourse","Global Korea Scholarship (GKS) — voie ambassade","KR","TOUS",
  "licence,master,doctorat","tous domaines","Scolarité + 900 000 KRW/mois + vols + année de coréen",
  None,"https://www.studyinkorea.go.kr",TODAY),
 ("bourse","Bourse du gouvernement chinois (CSC)","CN","TOUS",
  "licence,master,doctorat","tous domaines","Scolarité + logement + 2 500-3 500 CNY/mois",
  None,"https://www.campuschina.org",TODAY),
 ("bourse","France Excellence Eiffel","FR","TOUS",
  "master,doctorat","tous domaines","~1 000-1 700 EUR/mois selon niveau",
  None,"https://www.campusfrance.org/fr/le-programme-de-bourses-eiffel",TODAY),
 ("bourse","JICA — Initiative ABE (jeunes professionnels africains)","JP",
  "CM,GA,SN,CI,CD,HT,NG,GH,KE,ET","master","tous domaines",
  "Scolarité master + ~143 000 JPY/mois + stage en entreprise",
  None,"https://www.jica.go.jp",TODAY),
 ("formation","Licence/BUT via plateforme Études en France (~350 établissements)","FR",
  "CM,GA,HT,SN,CI,CD,VN,CN,IN","lycee,licence","tous domaines",
  "Frais publics réduits (droits différenciés possibles)",
  "2026-03-12","https://pastel.diplomatie.gouv.fr/etudesenfrance",TODAY),
 ("emploi","Jobs étudiants — Jobaviz (CROUS, ~70 000 annonces)","FR","TOUS",
  "licence,master","tous secteurs","SMIC horaire minimum, ≤964 h/an pour non-UE",
  None,"https://www.jobaviz.fr",TODAY),
 ("emploi","Offres France Travail (API publique)","FR","TOUS",
  "licence,master,pro","tous secteurs","Variable",
  None,"https://francetravail.io",TODAY),
 ("stage","Stages & alternance — 1jeune1solution (gouvernement FR)","FR","TOUS",
  "licence,master","tous secteurs","Gratification légale minimum",
  None,"https://www.1jeune1solution.gouv.fr",TODAY),
 ("formation","Programmes anglophones — établissements SEVP (visa F-1)","US","TOUS",
  "licence,master,doctorat","tous domaines","40 000-90 000+ USD/an à prouver (I-20)",
  None,"https://studyinthestates.dhs.gov",TODAY),
]

def main():
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.executescript(SCHEMA)
    n = cur.execute("SELECT COUNT(*) FROM opportunites").fetchone()[0]
    if n == 0:
        cur.executemany(
          "INSERT INTO opportunites(type,titre,destination,origines_eligibles,"
          "niveau,domaine,montant,deadline,source_url,maj) VALUES(?,?,?,?,?,?,?,?,?,?)",
          DEMO)
        print(f"OK : {len(DEMO)} opportunités d'exemple insérées.")
    else:
        print(f"Table déjà peuplée ({n} lignes) — rien à faire.")
    con.commit(); con.close()

if __name__ == "__main__":
    main()
