.PHONY: help install migrate run test lint clean superuser fixtures

help:
	@echo "Commandes disponibles:"
	@echo "  make install    - Installer les dépendances"
	@echo "  make migrate    - Appliquer les migrations"
	@echo "  make run        - Lancer le serveur de développement"
	@echo "  make test       - Lancer les tests"
	@echo "  make lint       - Vérifier le code"
	@echo "  make superuser  - Créer un superuser"
	@echo "  make fixtures   - Charger les données initiales"
	@echo "  make clean      - Nettoyer les fichiers temporaires"
	@echo "  make setup      - Installation complète"

install:
	pip install -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python manage.py runserver

test:
	pytest -v

lint:
	ruff check .

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

superuser:
	python manage.py createsuperuser

fixtures:
	python manage.py loaddata fixtures/initial_data.json

setup: install migrate fixtures
	@echo "Setup terminé! Lancez 'make run' pour démarrer le serveur."
