#!/bin/zsh
# ranger_feuille_route_v1.sh
# Cherche la feuille de route téléchargée et la place dans ~/mobilite-ia/data/
# Usage : zsh ranger_feuille_route_v1.sh

set -e

CIBLE="$HOME/mobilite-ia/data/feuille_route_italie_belgique_mcf_v1.md"
EMPREINTE="FEUILLE DE ROUTE"   # chaîne présente dans le fichier

echo "=== ranger_feuille_route_v1 ==="

# 1. Chercher par nom exact d'abord
TROUVE=$(find "$HOME/Downloads" -maxdepth 3 \
  -name "feuille route italie belgique mcf v1*" \
  -o -name "feuille_route_italie_belgique_mcf_v1*" \
  2>/dev/null | head -1)

# 2. Si pas trouvé, chercher par contenu (renommé par le navigateur)
if [[ -z "$TROUVE" ]]; then
  echo "Nom exact non trouvé — recherche par contenu..."
  TROUVE=$(grep -rl "$EMPREINTE" "$HOME/Downloads" \
    --include="*.md" --include="*.txt" \
    2>/dev/null | head -1)
fi

if [[ -z "$TROUVE" ]]; then
  echo "❌ Fichier introuvable dans ~/Downloads (maxdepth 3)."
  echo "   Vérifie que le téléchargement est terminé, puis relance."
  exit 1
fi

echo "✅ Trouvé : $TROUVE"

# 3. Vérifier que la cible n'existe pas déjà (identique → on skippe)
if [[ -f "$CIBLE" ]]; then
  if diff -q "$TROUVE" "$CIBLE" &>/dev/null; then
    echo "ℹ️  Fichier identique déjà en place : $CIBLE"
    echo "   Rien à faire."
    exit 0
  else
    BAK="${CIBLE%.md}.bak-$(date +%Y%m%d-%H%M%S).md"
    echo "⚠️  Version différente déjà présente → sauvegarde : $BAK"
    cp "$CIBLE" "$BAK"
  fi
fi

# 4. Copier (on garde l'original dans Downloads)
cp "$TROUVE" "$CIBLE"
echo "✅ Installé : $CIBLE"
echo "=== Terminé ==="
