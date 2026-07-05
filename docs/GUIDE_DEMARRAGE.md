# GUIDE DE DÉMARRAGE — Mobilité-IA sur ton Mac
### Les commandes exactes, la routine de suivi, et où ranger chaque fichier.

---

## 1. OÙ RANGER LE DOSSIER

Décompresse `mobilite-ia-kit.zip` puis place tout dans **`~/mobilite-ia`**
(ton dossier personnel → mobilite-ia). Arborescence finale :

```
~/mobilite-ia/
├── Makefile                      ← toutes tes commandes passent par lui
├── bootstrap_mobilite.sh         ← installation (à lancer UNE fois)
├── docs/                         ← la connaissance du projet
│   ├── PLAN_MOBILITE_IA.md       ← plan directeur (source de vérité)
│   ├── ANNEXE_CORRIDORS.md       ← modèle corridors (Annexe A)
│   ├── ANNEXE_B_MATRICE_MONDIALE.md  ← matrice tous pays (Annexe B)
│   └── GUIDE_DEMARRAGE.md        ← ce fichier
├── scripts/
│   ├── gen_matrice.py            ← génère les 7 440 corridors
│   ├── seed_demo.py              ← 10 opportunités réelles d'exemple
│   └── suivi.py                  ← le suivi du projet (make suivi)
├── app/
│   ├── api/ui.py                 ← le DASHBOARD (make dashboard)
│   ├── collectors/  normalizers/  rag/  agents/  billing/
├── data/                         ← créé automatiquement (JAMAIS dans git)
│   ├── mobilite.db               ← ta base SQLite (corridors + opportunités)
│   └── raw/  clean/  chroma/
└── backups/                      ← sauvegardes chiffrées (make backup)
```

Astuce rangement Mac : garde ce ZIP d'origine dans `~/Documents/Archives-Projets/`
comme copie de secours, et travaille uniquement dans `~/mobilite-ia`.

---

## 2. INSTALLATION (une seule fois, ~15 min)

Ouvre **Terminal** (Cmd+Espace → « Terminal ») :

```bash
cd ~/Downloads                      # là où tu as décompressé le kit
mv mobilite-ia-kit ~/mobilite-ia    # range le dossier au bon endroit
cd ~/mobilite-ia
chmod +x bootstrap_mobilite.sh
./bootstrap_mobilite.sh             # installe Homebrew, Python, Ollama, modèles
```

Puis initialise la matrice et les exemples :

```bash
source .venv/bin/activate
pip install pycountry
python scripts/gen_matrice.py       # → 7 440 corridors dans data/mobilite.db
python scripts/seed_demo.py         # → 10 opportunités réelles d'exemple
```

---

## 3. LE SUIVI DU PROJET — TA COMMANDE QUOTIDIENNE

```bash
cd ~/mobilite-ia
make suivi
```

Ça affiche en 2 secondes :
- ✅ tâches terminées / restantes du plan (barre de progression)
- 🌍 état de la matrice (corridors vérifiés, fiches destination prêtes)
- 🎯 opportunités en base par type + alertes de fraîcheur (> 90 jours)
- → les 3 prochaines actions à faire

## 4. LES 7 COMMANDES À CONNAÎTRE (c'est tout)

| Commande | Ce qu'elle fait | Quand |
|---|---|---|
| `make suivi` | État complet du projet | Chaque matin |
| `make plan` | Les 5 prochaines tâches T-xxx | Avant de travailler |
| `make agent` | Ton LLM local exécute la prochaine tâche et coche le plan | Quand tu veux avancer sans coder |
| `make collect` | Lance les collecteurs de données (bourses, offres…) | 1×/jour (automatisable) |
| `make index` | Ré-indexe la base RAG | Après collect |
| `make dashboard` | Ouvre le TABLEAU DE BORD dans le navigateur | Pour explorer les opportunités |
| `make backup` | Sauvegarde chiffrée de data/ | 1×/semaine |

Automatisation : pour que `collect + index` tournent seuls chaque matin à 6 h,
c'est la tâche T-00x du plan (launchd) — ton agent local peut la faire : `make agent`.

---

## 5. LE DASHBOARD DES OPPORTUNITÉS

```bash
make dashboard        # équivaut à : streamlit run app/api/ui.py
```
→ s'ouvre sur http://localhost:8501 dans ton navigateur.

Tu peux filtrer par :
- **Pays de destination** (les 30 : FR, CA, US, JP, KR…)
- **Pays d'origine** (code ISO : GA, CM, HT, IN…) — ne montre que ce qui est éligible
- **Type** : formation / bourse / emploi / stage
- **Niveau** : lycée, licence, master, doctorat, pro
- **Domaine** : informatique, santé, gestion…

Il affiche aussi : compteurs, ⏰ deadlines sous 45 jours, la source + date de
vérification de chaque fiche, et l'état de la matrice pour le pays d'origine choisi.

Le dashboard se remplit tout seul au fil des `make collect` : plus tes collecteurs
tournent, plus il devient riche. Les 10 lignes d'exemple (MEXT, GKS, CSC, Eiffel,
Jobaviz…) sont là pour que tu voies le résultat dès aujourd'hui.

---

## 6. ROUTINE TYPE D'UNE SEMAINE

```
Lundi     make suivi → make agent (×2-3)      # avancer le plan
Mardi     make collect && make index          # données fraîches
Mercredi  make dashboard                      # explorer, repérer les deadlines
Jeudi     make agent                          # continuer les tâches
Vendredi  make suivi && make backup           # bilan + sauvegarde
          git log --oneline | head            # voir l'historique de la semaine
```

## 7. SI QUELQUE CHOSE CASSE
- `make suivi` dit que la base est absente → `python scripts/gen_matrice.py`
- Le dashboard est vide → `python scripts/seed_demo.py` puis `make collect`
- Ollama ne répond pas → `brew services restart ollama`
- Revenir en arrière → `git log` puis `git checkout <commit> -- <fichier>`
