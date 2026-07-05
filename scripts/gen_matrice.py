#!/usr/bin/env python3
# =============================================================================
# gen_matrice.py — Génère la matrice mondiale de corridors (T-070)
# Toutes les origines ISO-3166 × 30 destinations → SQLite data/mobilite.db
# Usage :  python scripts/gen_matrice.py
# Dépendance : pip install pycountry
# =============================================================================
import sqlite3, datetime, sys
try:
    import pycountry
except ImportError:
    sys.exit("pip install pycountry --puis relance")

DB = "data/mobilite.db"
TODAY = datetime.date.today().isoformat()

# ---- 30 DESTINATIONS (tier, points d'entrée des fiches gabarit) -------------
DESTINATIONS = {
    # code: (nom, tier, procédure_type, note_amorce)
    "FR": ("France", 1, "etudes_en_france|dap|parcoursup", "7380 EUR/an; AVI ~470 EUR"),
    "CA": ("Canada", 1, "ircc_pal|ircc_caq", "22895 CAD hors QC + scolarité; QC 24617 CAD (01/2026); plafond 2026"),
    "US": ("Etats-Unis", 1, "f1_sevp", "I-20 40-90k USD/an; SEVIS 350 USD; MRV 185 USD; OPT 12/36 mois; risque 214(b)"),
    "GB": ("Royaume-Uni", 1, "student_visa_points", "CAS + fonds Londres/hors Londres + IHS"),
    "DE": ("Allemagne", 1, "sperrkonto_uniassist", "compte bloqué ~11.9k EUR/an (a verifier)"),
    "BE": ("Belgique", 1, "equivalence_fwb", "equivalence diplomes FWB"),
    "AU": ("Australie", 1, "genuine_student", "fonds eleves; marche agents structure"),
    "JP": ("Japon", 2, "coe_visa", "MEXT: scolarite + 143-145k JPY/mois; JICA ABE ~300 Africains/an"),
    "KR": ("Coree du Sud", 2, "d2_visa", "GKS: scolarite + 900k KRW/mois; ~1500/an; voie ambassade"),
    "CN": ("Chine", 2, "x1_visa", "CSC: scolarite + 2500-3500 CNY/mois; 289 universites"),
    "TR": ("Turquie", 2, "turkiye_burslari", "bourse complete gouvernementale"),
    "MY": ("Malaisie", 2, "emgs", "cout faible; hubs anglophones"),
    "MA": ("Maroc", 2, "amci", "bourses AMCI pour Afrique"),
    "TN": ("Tunisie", 2, "cooperation", "cout faible francophone"),
    "RU": ("Russie", 2, "quota_gouv", "quotas gouvernementaux"),
    "IN": ("Inde", 2, "iccr", "bourses ICCR"),
    "SA": ("Arabie saoudite", 2, "bourses_gouv", "bourses islamiques/univ."),
    "QA": ("Qatar", 2, "bourses_gouv", "Education City"),
    "AE": ("Emirats", 2, "univ_direct", "campus delocalises"),
    "HU": ("Hongrie", 2, "stipendium", "Stipendium Hungaricum"),
    "PL": ("Pologne", 3, "uni_direct", ""), "RO": ("Roumanie", 3, "uni_direct", ""),
    "NL": ("Pays-Bas", 3, "uni_direct", ""), "ES": ("Espagne", 3, "uni_direct", ""),
    "IT": ("Italie", 3, "uni_direct", ""), "PT": ("Portugal", 3, "uni_direct", ""),
    "CH": ("Suisse", 3, "uni_direct", ""), "SE": ("Suede", 3, "uni_direct", ""),
    "IE": ("Irlande", 3, "uni_direct", ""), "NZ": ("Nouvelle-Zelande", 3, "uni_direct", ""),
}

# ---- Pays « procédure Études en France » (liste officielle, à re-vérifier) --
EEF = {"ZA","AO","AM","AZ","DZ","SA","AR","BH","BJ","MM","BO","BR","BF","BI","KH",
       "CM","CA","CL","CN","CO","KM","CG","KR","CI","DJ","AE","EG","EC","US","ET",
       "GA","GE","GH","GN","HT","HK","IN","ID","IR","IL","JP","JO","KE","KW","LB",
       "MG","MY","ML","MA","MU","MR","MX","NP","NG","PK","PE","QA","CF","CD","DO",
       "GB","RU","RW","SN","SG","TW","TD","TH","TG","TN","TR","UA","VN"}

# ---- Zones tarifaires par défaut (affinées ensuite en T-073) -----------------
Z1 = {"HT","CD","MG","NE","TD","CF","BI","SO","SS","AF","MW","MZ","SL","LR","GN","GW","ML","BF","ET","YE","SD"}
Z3 = {"CN","MA","DZ","TN","TR","BR","MX","AR","CL","MY","TH","ZA","IN_URBAIN","RU","SA","QA","AE","KW","BH","OM"}
def zone(code): return "Z1" if code in Z1 else ("Z3" if code in Z3 else "Z2")

SCHEMA = """
CREATE TABLE IF NOT EXISTS destinations(
  code TEXT PRIMARY KEY, nom TEXT, tier INT, procedure TEXT,
  fiche TEXT, statut TEXT DEFAULT 'a_verifier', maj TEXT, sources TEXT);
CREATE TABLE IF NOT EXISTS origines(
  code TEXT PRIMARY KEY, nom TEXT, region TEXT, procedure_fr TEXT,
  zone_tarif TEXT, paiement TEXT, langues TEXT, concurrence TEXT,
  diaspora_payeuse INT, maj TEXT);
CREATE TABLE IF NOT EXISTS corridors(
  origine TEXT, destination TEXT, score INT DEFAULT 0,
  statut TEXT DEFAULT 'a_verifier', specificites TEXT, maj TEXT,
  PRIMARY KEY(origine, destination));
"""

def main():
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.executescript(SCHEMA)
    for code,(nom,tier,proc,note) in DESTINATIONS.items():
        cur.execute("INSERT OR IGNORE INTO destinations VALUES(?,?,?,?,?,?,?,?)",
                    (code,nom,tier,proc,note,"a_verifier",TODAY,""))
    n_orig = 0
    for c in pycountry.countries:
        code = c.alpha_2
        cur.execute("INSERT OR IGNORE INTO origines VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (code, c.name, "", "eef" if code in EEF else "hors_eef",
                     zone(code), "", "", "", 0, TODAY))
        for d in DESTINATIONS:
            if d != code:
                cur.execute("INSERT OR IGNORE INTO corridors(origine,destination,maj) VALUES(?,?,?)",
                            (code, d, TODAY))
        n_orig += 1
    con.commit()
    total = cur.execute("SELECT COUNT(*) FROM corridors").fetchone()[0]
    print(f"OK : {n_orig} origines x {len(DESTINATIONS)} destinations = {total} corridors generes (statut a_verifier).")
    print("Prochaine etape (agents locaux) : remplir les fiches par ordre de score — voir Annexe B5.")
    con.close()

if __name__ == "__main__":
    main()
