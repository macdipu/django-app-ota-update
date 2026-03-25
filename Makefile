COMPOSE = docker compose -f docker/compose/local.yml

.PHONY: up down rebuild migrate makemigrations shell logs test superuser clean

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

rebuild:
	$(COMPOSE) build --no-cache

migrate:
	$(COMPOSE) run --rm web python manage.py migrate

makemigrations:
	$(COMPOSE) run --rm web python manage.py makemigrations

shell:
	$(COMPOSE) run --rm web python manage.py shell

logs:
	$(COMPOSE) logs -f

test:
	$(COMPOSE) run --rm web pytest

superuser:
	$(COMPOSE) run --rm web python manage.py createsuperuser

collectstatic:
	$(COMPOSE) run --rm web python manage.py collectstatic --noinput

clean:
	$(COMPOSE) down -v
