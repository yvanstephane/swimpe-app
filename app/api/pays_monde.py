# =============================================================================
# pays_monde.py — TOUS les pays du monde comme pays d'ORIGINE
# (nom français → (code ISO, devise pour l'affichage du prix d'appel))
# Les destinations restent la liste maîtrisée dans ui.py (activable en admin).
# =============================================================================

ORIGINES_MONDE = {
 # ---------------- Europe ----------------
 "Albanie":("AL","EUR"),"Allemagne":("DE","EUR"),"Andorre":("AD","EUR"),
 "Autriche":("AT","EUR"),"Biélorussie":("BY","USD"),"Belgique":("BE","EUR"),
 "Bosnie-Herzégovine":("BA","EUR"),"Bulgarie":("BG","EUR"),"Chypre":("CY","EUR"),
 "Croatie":("HR","EUR"),"Danemark":("DK","EUR"),"Espagne":("ES","EUR"),
 "Estonie":("EE","EUR"),"Finlande":("FI","EUR"),"France":("FR","EUR"),
 "Grèce":("GR","EUR"),"Hongrie":("HU","EUR"),"Irlande":("IE","EUR"),
 "Islande":("IS","EUR"),"Italie":("IT","EUR"),"Kosovo":("XK","EUR"),
 "Lettonie":("LV","EUR"),"Liechtenstein":("LI","EUR"),"Lituanie":("LT","EUR"),
 "Luxembourg":("LU","EUR"),"Macédoine du Nord":("MK","EUR"),"Malte":("MT","EUR"),
 "Moldavie":("MD","EUR"),"Monaco":("MC","EUR"),"Monténégro":("ME","EUR"),
 "Norvège":("NO","EUR"),"Pays-Bas":("NL","EUR"),"Pologne":("PL","EUR"),
 "Portugal":("PT","EUR"),"République tchèque":("CZ","EUR"),"Roumanie":("RO","EUR"),
 "Royaume-Uni":("GB","GBP"),"Russie":("RU","USD"),"Saint-Marin":("SM","EUR"),
 "Serbie":("RS","EUR"),"Slovaquie":("SK","EUR"),"Slovénie":("SI","EUR"),
 "Suède":("SE","EUR"),"Suisse":("CH","EUR"),"Ukraine":("UA","USD"),

 # ---------------- Afrique ----------------
 "Afrique du Sud":("ZA","ZAR"),"Algérie":("DZ","EUR"),"Angola":("AO","USD"),
 "Bénin":("BJ","XOF"),"Botswana":("BW","USD"),"Burkina Faso":("BF","XOF"),
 "Burundi":("BI","USD"),"Cameroun":("CM","XAF"),"Cap-Vert":("CV","EUR"),
 "Comores":("KM","EUR"),"Congo (Brazzaville)":("CG","XAF"),"Congo (RDC)":("CD","CDF"),
 "Côte d'Ivoire":("CI","XOF"),"Djibouti":("DJ","USD"),"Égypte":("EG","EGP"),
 "Érythrée":("ER","USD"),"Eswatini":("SZ","ZAR"),"Éthiopie":("ET","USD"),
 "Gabon":("GA","XAF"),"Gambie":("GM","USD"),"Ghana":("GH","GHS"),
 "Guinée":("GN","USD"),"Guinée-Bissau":("GW","XOF"),"Guinée équatoriale":("GQ","XAF"),
 "Kenya":("KE","KES"),"Lesotho":("LS","ZAR"),"Libéria":("LR","USD"),
 "Libye":("LY","USD"),"Madagascar":("MG","EUR"),"Malawi":("MW","USD"),
 "Mali":("ML","XOF"),"Maroc":("MA","MAD"),"Maurice":("MU","EUR"),
 "Mauritanie":("MR","EUR"),"Mozambique":("MZ","USD"),"Namibie":("NA","ZAR"),
 "Niger":("NE","XOF"),"Nigeria":("NG","NGN"),"Ouganda":("UG","USD"),
 "République centrafricaine":("CF","XAF"),"Rwanda":("RW","RWF"),
 "São Tomé-et-Principe":("ST","EUR"),"Sénégal":("SN","XOF"),"Seychelles":("SC","EUR"),
 "Sierra Leone":("SL","USD"),"Somalie":("SO","USD"),"Soudan":("SD","USD"),
 "Soudan du Sud":("SS","USD"),"Tanzanie":("TZ","USD"),"Tchad":("TD","XAF"),
 "Togo":("TG","XOF"),"Tunisie":("TN","TND"),"Zambie":("ZM","USD"),
 "Zimbabwe":("ZW","USD"),

 # ---------------- Amériques ----------------
 "Antigua-et-Barbuda":("AG","USD"),"Argentine":("AR","USD"),"Bahamas":("BS","USD"),
 "Barbade":("BB","USD"),"Belize":("BZ","USD"),"Bolivie":("BO","USD"),
 "Brésil":("BR","BRL"),"Canada":("CA","CAD"),"Chili":("CL","USD"),
 "Colombie":("CO","USD"),"Costa Rica":("CR","USD"),"Cuba":("CU","USD"),
 "Dominique":("DM","USD"),"Équateur":("EC","USD"),"États-Unis":("US","USD"),
 "Grenade":("GD","USD"),"Guatemala":("GT","USD"),"Guyana":("GY","USD"),
 "Haïti":("HT","HTG"),"Honduras":("HN","USD"),"Jamaïque":("JM","USD"),
 "Mexique":("MX","USD"),"Nicaragua":("NI","USD"),"Panama":("PA","USD"),
 "Paraguay":("PY","USD"),"Pérou":("PE","USD"),"République dominicaine":("DO","USD"),
 "Sainte-Lucie":("LC","USD"),"Saint-Kitts-et-Nevis":("KN","USD"),
 "Saint-Vincent-et-les-Grenadines":("VC","USD"),"Salvador":("SV","USD"),
 "Suriname":("SR","USD"),"Trinité-et-Tobago":("TT","USD"),"Uruguay":("UY","USD"),
 "Venezuela":("VE","USD"),

 # ---------------- Asie & Moyen-Orient ----------------
 "Afghanistan":("AF","USD"),"Arabie Saoudite":("SA","USD"),"Arménie":("AM","USD"),
 "Azerbaïdjan":("AZ","USD"),"Bahreïn":("BH","USD"),"Bangladesh":("BD","USD"),
 "Bhoutan":("BT","INR"),"Birmanie (Myanmar)":("MM","USD"),"Brunei":("BN","USD"),
 "Cambodge":("KH","USD"),"Chine":("CN","USD"),"Corée du Nord":("KP","USD"),
 "Corée du Sud":("KR","USD"),"Émirats Arabes Unis":("AE","USD"),
 "Géorgie":("GE","USD"),"Inde":("IN","INR"),"Indonésie":("ID","IDR"),
 "Irak":("IQ","USD"),"Iran":("IR","USD"),"Israël":("IL","USD"),
 "Japon":("JP","USD"),"Jordanie":("JO","USD"),"Kazakhstan":("KZ","USD"),
 "Kirghizistan":("KG","USD"),"Koweït":("KW","USD"),"Laos":("LA","USD"),
 "Liban":("LB","USD"),"Malaisie":("MY","USD"),"Maldives":("MV","USD"),
 "Mongolie":("MN","USD"),"Népal":("NP","USD"),"Oman":("OM","USD"),
 "Ouzbékistan":("UZ","USD"),"Pakistan":("PK","PKR"),"Palestine":("PS","USD"),
 "Philippines":("PH","USD"),"Qatar":("QA","USD"),"Singapour":("SG","USD"),
 "Sri Lanka":("LK","USD"),"Syrie":("SY","USD"),"Tadjikistan":("TJ","USD"),
 "Taïwan":("TW","USD"),"Thaïlande":("TH","USD"),"Timor oriental":("TL","USD"),
 "Turkménistan":("TM","USD"),"Turquie":("TR","USD"),"Vietnam":("VN","USD"),
 "Yémen":("YE","USD"),

 # ---------------- Océanie ----------------
 "Australie":("AU","USD"),"Fidji":("FJ","USD"),"Kiribati":("KI","USD"),
 "Îles Marshall":("MH","USD"),"Micronésie":("FM","USD"),"Nauru":("NR","USD"),
 "Nouvelle-Zélande":("NZ","USD"),"Palaos":("PW","USD"),
 "Papouasie-Nouvelle-Guinée":("PG","USD"),"Îles Salomon":("SB","USD"),
 "Samoa":("WS","USD"),"Tonga":("TO","USD"),"Tuvalu":("TV","USD"),
 "Vanuatu":("VU","USD"),
}
