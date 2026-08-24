.PHONY: help install db-up db-wait db-down db-reset migrate run eval

help:
	@echo "make run       - start Postgres, apply migrations, launch the Streamlit app"
	@echo "make eval      - start Postgres, apply migrations, run the eval harness"
	@echo "make install   - install dependencies (uv sync)"
	@echo "make db-down   - stop Postgres"
	@echo "make db-reset  - stop Postgres and delete its data volume"

install:
	uv sync

db-up:
	docker compose up -d postgres

db-wait: db-up
	@until docker compose ps postgres | grep -q healthy; do sleep 1; done

migrate: db-wait
	uv run alembic upgrade head

run: install migrate
	uv run streamlit run streamlit_app.py --server.headless true

eval: install migrate
	uv run python -m worksmith.evals.run

db-down:
	docker compose down

db-reset:
	docker compose down -v
