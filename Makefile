COMPOSE = docker compose -f docker/compose/local.yml

.PHONY: up down rebuild migrate makemigrations shell logs test superuser clean deps

up:
	$(COMPOSE) up --build

deps:
	$(COMPOSE) up -d db minio

down:
	$(COMPOSE) down

rebuild:
	$(COMPOSE) build --no-cache

migrate:
	$(COMPOSE) run --rm app python manage.py migrate --noinput

makemigrations:
	$(COMPOSE) run --rm app python manage.py makemigrations

shell:
	$(COMPOSE) run --rm app python manage.py shell

logs:
	$(COMPOSE) logs -f

test:
	$(COMPOSE) run --rm app pytest

superuser:
	$(COMPOSE) run --rm app python manage.py createsuperuser

collectstatic:
	$(COMPOSE) run --rm app python manage.py collectstatic --noinput

clean:
	$(COMPOSE) down -v
