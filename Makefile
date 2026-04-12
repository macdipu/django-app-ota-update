COMPOSE_LOCAL = docker compose --env-file .env -f docker/compose/local.yml
COMPOSE_PROD = docker compose --env-file .env -f docker/compose/prod.yml

.PHONY: up down rebuild migrate makemigrations shell logs test superuser clean deps collectstatic prod-up prod-down prod-logs

up:
	$(COMPOSE_LOCAL) up --build

deps:
	$(COMPOSE_LOCAL) up -d db minio

down:
	$(COMPOSE_LOCAL) down

rebuild:
	$(COMPOSE_LOCAL) build --no-cache

migrate:
	$(COMPOSE_LOCAL) run --rm app python manage.py migrate --noinput

makemigrations:
	$(COMPOSE_LOCAL) run --rm app python manage.py makemigrations

shell:
	$(COMPOSE_LOCAL) run --rm app python manage.py shell

logs:
	$(COMPOSE_LOCAL) logs -f

test:
	$(COMPOSE_LOCAL) run --rm app pytest

superuser:
	$(COMPOSE_LOCAL) run --rm app python manage.py createsuperuser

collectstatic:
	$(COMPOSE_LOCAL) run --rm app python manage.py collectstatic --noinput

clean:
	$(COMPOSE_LOCAL) down -v

prod-up:
	$(COMPOSE_PROD) up --build -d

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f
