# Documentation Technique - Véhicules d'Occasion

## Architecture du Projet

```
backend/
├── config/                 # Configuration Django
│   ├── settings.py        # Paramètres Django
│   ├── urls.py            # URLs racine
│   ├── api.py             # Configuration Django Ninja
│   └── wsgi.py / asgi.py  # Entry points
│
├── core/                   # Module central
│   ├── models.py          # BaseModel, SoftDelete, AuditLog
│   └── services.py        # AuditService
│
├── users/                  # Gestion utilisateurs
│   ├── models.py          # User, Profile, Address
│   ├── schemas.py         # Schémas Ninja
│   ├── services.py        # Logique métier
│   └── api.py             # Endpoints
│
├── vehicles/               # Catalogue véhicules
│   ├── models.py          # Vehicle, Media, Spec, History
│   ├── schemas.py
│   ├── services.py
│   └── api.py
│
├── inventory/              # Gestion du stock
│   ├── models.py          # InventoryItem, InventoryLog
│   ├── schemas.py
│   ├── services.py
│   └── api.py
│
├── wishlist/               # Liste de souhaits
├── cart/                   # Panier
├── orders/                 # Commandes
├── billing/                # Facturation & Paiements
├── reviews/                # Avis clients
│
├── tests/                  # Tests
└── fixtures/               # Données initiales
```

## Stack Technique

- **Python 3.12+**
- **Django 5.0** (LTS)
- **Django Ninja** (API REST)
- **PostgreSQL** (production) / SQLite (dev)
- **JWT** pour l'authentification API
- **pytest** pour les tests

## Modèles de Données

### Hiérarchie des modèles de base

```python
BaseModel
├── UUIDModel (UUID primary key)
├── TimestampedModel (created_at, updated_at)
└── SoftDeleteModel (is_deleted, deleted_at)
```

### Relations principales

```
User ─┬─> Profile (1:1)
      ├─> Address (1:N)
      ├─> Cart (1:N)
      ├─> Wishlist (1:1)
      ├─> Order (1:N)
      └─> Review (1:N)

Vehicle ─┬─> VehicleMedia (1:N)
         ├─> VehicleSpecification (1:N)
         ├─> VehicleHistory (1:1)
         └─> InventoryItem (1:1)

Order ─┬─> OrderItem (1:N)
       ├─> Invoice (1:1)
       └─> Payment (1:N)
```

## API Endpoints

### Authentification

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/token/pair` | POST | Obtenir JWT |
| `/api/v1/token/refresh` | POST | Rafraîchir JWT |

### Utilisateurs

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/api/v1/users/register` | POST | Non | Inscription |
| `/api/v1/users/me` | GET | Oui | Profil utilisateur |
| `/api/v1/users/me` | PATCH | Oui | Modifier profil |
| `/api/v1/users/me/addresses` | GET/POST | Oui | Adresses |

### Véhicules

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/api/v1/vehicles/` | GET | Non | Liste (filtres, pagination) |
| `/api/v1/vehicles/{id}` | GET | Non | Détails |
| `/api/v1/vehicles/featured` | GET | Non | Mis en avant |
| `/api/v1/vehicles/` | POST | Admin | Créer |

### Panier

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/cart/` | GET | Voir panier |
| `/api/v1/cart/items` | POST | Ajouter |
| `/api/v1/cart/items/{id}` | DELETE | Retirer |

### Commandes

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/orders/` | GET | Liste commandes |
| `/api/v1/orders/` | POST | Créer depuis panier |
| `/api/v1/orders/{id}` | GET | Détails |
| `/api/v1/orders/{id}/cancel` | POST | Annuler |

### Paiements

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/billing/orders/{id}/pay` | POST | Initier paiement |
| `/api/v1/billing/payments/{id}/mock-pay` | POST | Simuler paiement (dev) |

## Sécurité

### Rôles utilisateurs

- **CLIENT**: Peut consulter, acheter, laisser des avis
- **SELLER**: Peut gérer les véhicules
- **ADMIN**: Accès complet

### Authentification hybride

- **Session Django**: Admin Django
- **JWT**: API REST

### Audit

Toutes les actions significatives sont tracées dans `AuditLog`:
- Création/modification/suppression d'entités
- Changements de statut
- Paiements
- Connexions

## Installation

```bash
# 1. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
cd backend
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 4. Appliquer les migrations
python manage.py migrate

# 5. Charger les fixtures
python manage.py loaddata fixtures/initial_data.json

# 6. Créer un superuser
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver
```

## Tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=.

# Tests spécifiques
pytest tests/test_users.py -v
```

## Développement avec SQLite

Pour utiliser SQLite au lieu de PostgreSQL:

```bash
# Dans .env
USE_SQLITE=True
```

## Documentation API

Accédez à la documentation interactive:
- Swagger UI: `http://localhost:8000/api/v1/docs`

## Commandes utiles

```bash
# Migrations
make migrate

# Tests
make test

# Créer superuser
make superuser

# Charger fixtures
make fixtures
```
