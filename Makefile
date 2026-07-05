suivi:
	.venv/bin/python scripts/suivi.py
plan:
	@grep -n "\[ \] T-" docs/*.md | head -5
agent:
	.venv/bin/python -m app.agents.executor --plan docs/PLAN_MOBILITE_IA.md
collect:
	.venv/bin/python -m app.collectors.run_all
index:
	.venv/bin/python -m app.rag.build_index
dashboard:
	.venv/bin/streamlit run app/api/ui.py
chat:
	.venv/bin/python -m app.agents.chat
backup:
	mkdir -p backups && tar czf - data | openssl enc -aes-256-cbc -pbkdf2 -out backups/data-$$(date +%F).tgz.enc
