#!/usr/bin/env python3
# =============================================================================
# genere_dashboard_securite.py — Génère le tableau de bord SOC (HTML/CSS/JS)
# Lit les événements de data/mobilite.db et produit un fichier HTML autonome.
# PRINCIPE DE CODAGE SÉCURISÉ appliqué : toutes les données insérées dans le
# HTML/JS sont échappées (json.dumps + html.escape) → aucune injection possible
# même si un événement contenait du HTML/JS malveillant.
# Usage : python scripts/genere_dashboard_securite.py
# Sortie : dashboard_securite.html (à ouvrir dans le navigateur)
# =============================================================================
import sys, os, json, html, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "api"))
import securite

def main():
    evts = securite.evenements(500)
    s = securite.stats()

    # ÉCHAPPEMENT : json.dumps neutralise tout contenu actif ; par sécurité
    # supplémentaire on échappe aussi chaque champ texte.
    for e in evts:
        for k in ("description", "acteur", "detail", "type"):
            e[k] = html.escape(str(e.get(k, "")))
    donnees_js = json.dumps(evts, ensure_ascii=False)

    page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Yorbity SOC — Monitoring de sécurité</title>
<style>
  :root {{
    --bg:#0b1220; --panel:#111a2e; --bord:#1e2a44; --txt:#e5eaf4; --mut:#8b98b8;
    --info:#3b82f6; --faible:#22c55e; --moyen:#eab308; --eleve:#f97316; --critique:#ef4444;
  }}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ background:var(--bg); color:var(--txt);
          font-family:-apple-system,'Segoe UI',Roboto,sans-serif; padding:24px; }}
  h1 {{ font-size:1.4rem; margin-bottom:4px; }}
  .sous {{ color:var(--mut); font-size:.85rem; margin-bottom:20px; }}
  .cartes {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
             gap:12px; margin-bottom:20px; }}
  .carte {{ background:var(--panel); border:1px solid var(--bord); border-radius:12px;
            padding:14px 16px; }}
  .carte .num {{ font-size:1.6rem; font-weight:700; }}
  .carte .lab {{ color:var(--mut); font-size:.78rem; }}
  .barre-sev {{ display:flex; height:10px; border-radius:6px; overflow:hidden;
                margin:6px 0 16px; border:1px solid var(--bord); }}
  .filtres {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px; }}
  select, input {{ background:var(--panel); color:var(--txt); border:1px solid var(--bord);
                   border-radius:8px; padding:8px 10px; font-size:.85rem; }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel);
           border:1px solid var(--bord); border-radius:12px; overflow:hidden; }}
  th, td {{ padding:9px 12px; text-align:left; font-size:.82rem;
            border-bottom:1px solid var(--bord); }}
  th {{ color:var(--mut); font-weight:600; background:#0e1730;
        position:sticky; top:0; }}
  tr:hover td {{ background:#16223c; }}
  .badge {{ padding:2px 9px; border-radius:999px; font-size:.72rem; font-weight:600; }}
  .b-info {{ background:#1e3a8a55; color:#93c5fd; }}
  .b-faible {{ background:#14532d55; color:#86efac; }}
  .b-moyen {{ background:#71360b55; color:#fde047; }}
  .b-eleve {{ background:#7c2d1255; color:#fdba74; }}
  .b-critique {{ background:#7f1d1d66; color:#fca5a5; }}
  .note {{ color:var(--mut); font-size:.75rem; margin-top:14px; }}
</style>
</head>
<body>
  <h1>🛡️ Yorbity SOC — Monitoring de sécurité</h1>
  <div class="sous">Tableau de bord défensif · généré le {html.escape(datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))} ·
       lecture seule · aucune donnée personnelle en clair (e-mails masqués, IP hachées)</div>

  <div class="cartes">
    <div class="carte"><div class="num">{s['total']}</div><div class="lab">Événements (total)</div></div>
    <div class="carte"><div class="num">{s['aujourdhui']}</div><div class="lab">Aujourd'hui</div></div>
    <div class="carte"><div class="num" style="color:var(--eleve)">{s['critiques']}</div><div class="lab">Alertes élevées / critiques</div></div>
    <div class="carte"><div class="num" id="affiches">–</div><div class="lab">Affichés (filtre)</div></div>
  </div>

  <div class="barre-sev" id="barreSev" title="Répartition par sévérité"></div>

  <div class="filtres">
    <select id="fSev">
      <option value="">Toutes sévérités</option>
      <option>info</option><option>faible</option><option>moyen</option>
      <option>eleve</option><option>critique</option>
    </select>
    <select id="fType"><option value="">Tous types</option></select>
    <input id="fTexte" placeholder="Rechercher (acteur, détail…)" size="28">
  </div>

  <table>
    <thead><tr>
      <th>Horodatage</th><th>Sévérité</th><th>Type</th>
      <th>Description</th><th>Acteur</th><th>IP (hash)</th><th>Détail</th>
    </tr></thead>
    <tbody id="corps"></tbody>
  </table>

  <div class="note">
    🔒 Principes appliqués : données échappées côté génération (anti-injection),
    e-mails masqués et IP hachées (vie privée / RGPD), lecture seule (aucune action
    exécutable depuis ce tableau). Règle de détection active : ≥5 échecs de connexion
    en 10 min → alerte « rafale » élevée.
  </div>

<script>
"use strict";
// Données injectées de façon SÛRE : sérialisation JSON (aucun code exécutable)
const EVENEMENTS = {donnees_js};

const corps = document.getElementById("corps");
const fSev = document.getElementById("fSev");
const fType = document.getElementById("fType");
const fTexte = document.getElementById("fTexte");

// Remplir le filtre des types
[...new Set(EVENEMENTS.map(e => e.type))].sort().forEach(t => {{
  const o = document.createElement("option"); o.textContent = t; fType.appendChild(o);
}});

// Échappement côté client aussi (défense en profondeur)
function esc(x) {{
  const d = document.createElement("div"); d.textContent = String(x ?? ""); return d.innerHTML;
}}

function rendre() {{
  const sev = fSev.value, typ = fType.value, q = fTexte.value.toLowerCase();
  const filtres = EVENEMENTS.filter(e =>
    (!sev || e.severite === sev) &&
    (!typ || e.type === typ) &&
    (!q || (e.acteur + " " + e.detail + " " + e.description).toLowerCase().includes(q))
  );
  document.getElementById("affiches").textContent = filtres.length;
  corps.innerHTML = filtres.map(e => `
    <tr>
      <td>${{esc(e.horodatage).replace("T","&nbsp;")}}</td>
      <td><span class="badge b-${{esc(e.severite)}}">${{esc(e.severite)}}</span></td>
      <td>${{esc(e.type)}}</td>
      <td>${{esc(e.description)}}</td>
      <td>${{esc(e.acteur)}}</td>
      <td><code>${{esc(e.ip_hash)}}</code></td>
      <td>${{esc(e.detail)}}</td>
    </tr>`).join("");
}}

// Barre de répartition des sévérités
(function() {{
  const ordre = ["info","faible","moyen","eleve","critique"];
  const cpt = Object.fromEntries(ordre.map(s => [s, 0]));
  EVENEMENTS.forEach(e => {{ if (cpt[e.severite] !== undefined) cpt[e.severite]++; }});
  const total = Math.max(1, EVENEMENTS.length);
  const barre = document.getElementById("barreSev");
  ordre.forEach(s => {{
    const seg = document.createElement("div");
    seg.style.width = (100 * cpt[s] / total) + "%";
    seg.style.background = getComputedStyle(document.documentElement)
                             .getPropertyValue("--" + s);
    seg.title = s + " : " + cpt[s];
    barre.appendChild(seg);
  }});
}})();

fSev.onchange = fType.onchange = rendre;
fTexte.oninput = rendre;
rendre();
</script>
</body>
</html>"""

    sortie = "dashboard_securite.html"
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"✓ Tableau de bord généré : {sortie}")
    print(f"  {len(evts)} événements · ouvre-le : open {sortie}")

if __name__ == "__main__":
    main()
