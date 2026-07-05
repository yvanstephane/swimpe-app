#!/bin/bash
# =============================================================================
# bootstrap_mobilite.sh — Amorçage du projet Mobilité-IA sur macOS
# Usage :  chmod +x bootstrap_mobilite.sh && ./bootstrap_mobilite.sh
# Idempotent : peut être relancé sans danger.
# =============================================================================
set -e
PROJECT="$HOME/mobilite-ia"

echo "==> 1/6 Vérification de Homebrew..."
if ! command -v brew >/dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "==> 2/6 Installation des outils (git, python, sqlite, ollama)..."
brew list git >/dev/null 2>&1 || brew install git
brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
brew list sqlite >/dev/null 2>&1 || brew install sqlite
brew list ollama >/dev/null 2>&1 || brew install ollama

echo "==> 3/6 Modèles locaux (choix selon RAM)..."
RAM_GB=$(($(sysctl -n hw.memsize) / 1073741824))
brew services start ollama 2>/dev/null || true
sleep 3
if [ "$RAM_GB" -ge 32 ]; then MAIN_MODEL="qwen2.5:14b"; else MAIN_MODEL="llama3.1:8b"; fi
echo "    RAM détectée: ${RAM_GB} Go → modèle principal: ${MAIN_MODEL}"
ollama pull "$MAIN_MODEL"
ollama pull mistral
ollama pull nomic-embed-text

echo "==> 4/6 Structure du projet dans $PROJECT ..."
mkdir -p "$PROJECT"/{app/{collectors,normalizers,rag,agents/prompts,api,billing,modules},data/{raw,clean,chroma},docs,scripts,backups,tests}
cd "$PROJECT"
[ -d .git ] || git init
cat > .gitignore <<'EOF'
.env
.venv/
data/
backups/
__pycache__/
*.db
EOF

echo "==> 5/6 Environnement Python..."
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip -q install --upgrade pip
./.venv/bin/pip -q install fastapi uvicorn typer streamlit chromadb requests \
  beautifulsoup4 pydantic feedparser python-dotenv httpx pandas ollama

echo "==> 6/6 Fichiers de base..."
cat > .env <<EOF
OLLAMA_HOST=http://localhost:11434
MAIN_MODEL=${MAIN_MODEL}
EXTRACT_MODEL=mistral
EMBED_MODEL=nomic-embed-text
EOF

cat > Makefile <<'EOF'
plan:
	@grep -n "\[ \] T-" docs/PLAN_MOBILITE_IA.md | head -5
collect:
	.venv/bin/python -m app.collectors.run_all
index:
	.venv/bin/python -m app.rag.build_index
agent:
	.venv/bin/python -m app.agents.executor --plan docs/PLAN_MOBILITE_IA.md
chat:
	.venv/bin/python -m app.agents.chat
ui:
	.venv/bin/streamlit run app/api/ui.py
backup:
	mkdir -p backups && tar czf - data | openssl enc -aes-256-cbc -pbkdf2 -out backups/data-$$(date +%F).tgz.enc
EOF

# Copie du plan s'il est à côté du script
[ -f "$(dirname "$0")/PLAN_MOBILITE_IA.md" ] && cp "$(dirname "$0")/PLAN_MOBILITE_IA.md" docs/

git add -A && git commit -m "Bootstrap projet Mobilité-IA" >/dev/null 2>&1 || true

echo ""
echo "✅ Terminé. Prochaines étapes :"
echo "   cd ~/mobilite-ia"
echo "   make plan        # voir les prochaines tâches"
echo "   ollama run ${MAIN_MODEL} \"bonjour\"   # tester le modèle"
