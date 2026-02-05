# Projet E‑commerce Véhicules d’Occasion – Spécifications Initiales

## 1. Objectif du projet

Application e‑commerce dédiée à **l’achat / revente de véhicules motorisés d’occasion** (voitures, motos, utilitaires, etc.).

Le projet vise un **niveau professionnel** :

* Modélisation réaliste des données
* Architecture modulaire et testable
* API claire, REST‑like, bien nommée
* Console admin exploitable manuellement dès le départ

Le dépôt démarre **vide** : ce document sert de **contrat fonctionnel et technique** pour générer le socle minimal.

---

## 2. Stack technique (Backend)

### 2.1 Technologies imposées

* **Python 3.12+**
* **Django** (LTS)
* **Django Ninja** (API REST)
* **ORM Django** (relationnel)
* Base de données : **PostgreSQL** (par défaut, configurable)
* Authentification : Django auth étendu

### 2.2 Architecture générale

* Architecture **modulaire par domaine métier**
* Chaque module expose :

  * models
  * schemas (Ninja)
  * routers (endpoints)
  * services (logique métier)
  * tests (unitaires & intégration)
- Exemple:
```
backend/
├── core/
├── users/
├── vehicles/
├── inventory/
├── wishlist/
├── cart/
├── orders/
├── billing/
├── reviews/
├── admin_custom/
├── tests/
└── fixtures/
```

---

## 3. Domaines fonctionnels & Modèles de données

### 3.1 Utilisateurs & Authentification

#### User (extension Django)

* id (UUID)
* email (unique)
* password
* first_name / last_name
* phone_number
* role (CLIENT | ADMIN | STAFF | SELLER)
* is_active
* date_joined
* last_login

#### Profile

* user (OneToOne)
* address (FK)
* billing_address (FK)
* preferences (JSON)

#### Address

* id
* user
* street
* city
* postal_code
* country
* is_default_shipping
* is_default_billing

CRUD complet + endpoints sécurisés.

---

### 3.2 Véhicules (Catalogue produit)

#### Vehicle

* id (UUID)
* title
* description
* brand
* model
* year
* mileage
* fuel_type
* transmission
* power_hp
* color
* condition (ENUM : neuf / excellent / bon / correct)
* price
* currency
* is_active
* created_at
* updated_at

#### VehicleMedia

* id
* vehicle (FK)
* media_type (IMAGE | VIDEO)
* url
* is_primary

#### VehicleSpecification

* id
* vehicle (FK)
* key
* value

CRUD complet.

---

### 3.3 Gestion du Stock

#### InventoryItem

* id
* vehicle (OneToOne)
* quantity (souvent 1)
* location
* status (AVAILABLE | RESERVED | SOLD)
* updated_at

Historique optionnel :

#### InventoryLog

* inventory_item
* previous_status
* new_status
* timestamp
* reason

---

### 3.4 Panier (Cart)

#### Cart

* id
* user
* status (ACTIVE | CONVERTED | ABANDONED)
* created_at

#### CartItem

* id
* cart
* vehicle
* price_snapshot
* added_at

Un véhicule ne peut être présent qu’une fois par panier.

---

### 3.5 Wishlist (Liste de souhaits)

#### Wishlist

* id
* user
* created_at

#### WishlistItem

* id
* wishlist
* vehicle
* added_at

---

### 3.6 Commandes & Achats

#### Order

* id
* user
* status (PENDING | PAID | CANCELLED | REFUNDED)
* total_amount
* currency
* created_at

#### OrderItem

* id
* order
* vehicle
* price_snapshot

---

### 3.7 Facturation & Paiements

#### Invoice

* id
* order
* invoice_number
* issued_at
* total_ht
* total_tva
* total_ttc

#### Payment

* id
* order
* provider
* provider_reference
* amount
* status (INITIATED | SUCCESS | FAILED)
* paid_at

---

### 3.8 Avis & Notations

#### Review

* id
* user
* vehicle
* rating (1–5)
* comment
* created_at

---

## 4. API Design

### 4.1 Bonnes pratiques

* Préfixe : `/api/v1/`
* Noms **pluriels**, clairs, cohérents
* HTTP verbs standards

Exemples :

* `GET /api/v1/vehicles/`
* `POST /api/v1/cart/items/`
* `PUT /api/v1/wishlist/{id}/`
* `DELETE /api/v1/wishlist/{id}/`

### 4.2 Sécurité

* JWT ou session (à définir)
* Permissions par rôle
* Validation stricte des payloads (schemas Ninja)

---

## 5. Admin Django

### Objectifs

* Admin **fonctionnel immédiatement**
* Gestion manuelle de :

  * users
  * vehicles
  * inventory
  * orders
  * payments

### Contraintes

* Admin custom léger
* Filtres, search, readonly fields
* Pas de front custom à ce stade

---

## 6. Tests

### Types de tests

* Unitaires :

  * modèles
  * services
* Intégration :

  * endpoints API
  * workflows (panier → commande → paiement)

### Outils

* pytest
* pytest-django

---

## 7. Fixtures

### Objectifs

* Base exploitable dès `loaddata`
* Données réalistes

### Contenu

* 5–10 utilisateurs
* 20+ véhicules
* Panier + wishlist pré-remplis
* Commandes payées / non payées

---

## 8. Performance & Async

* Async Ninja pour endpoints lourds (listing, recherche)
* Index DB sur :

  * price
  * brand / model
  * status

---

## 9. Ce qui n’est PAS inclus (pour l’instant)

* Frontend
* Paiement réel (Stripe mock uniquement)
* Internationalisation avancée
* Microservices

---

## 10. Décisions validées & clarifications

### 10.1 Authentification (clarification importante)

**Choix retenu : Authentification hybride**

* **Session Django** :

  * utilisée pour l’admin Django
  * utilisée pour les utilisateurs authentifiés classiques (CLIENT / ADMIN)
  * **ne gère pas d’utilisateurs sans compte** par défaut
* **JWT (Django Ninja)** :

  * utilisé pour l’API publique
  * requis pour toute action sensible (panier, wishlist, commandes)

👉 Les utilisateurs **sans compte** :

* peuvent uniquement consulter le catalogue (lecture seule)
* **pas de panier persistant**, pas de wishlist, pas d’achat

---

### 10.2 Hypothèses fonctionnelles validées

* **Stock** : stock unique (plateforme propriétaire, pas de multi-vendeurs)
* **Fiscalité** : mono-pays (TVA unique configurable)
* **Recherche** :

  * recherche texte simple
  * filtres basiques (catégorie, marque, prix)
  * pas de moteur full-text avancé
* **Historique véhicule** : OUI, modélisé
* **Rôles utilisateurs** : CLIENT / ADMIN uniquement
* **Suppression** : soft delete sur toutes les entités critiques
* **Logs & audit** : gestion standardisée et centralisée

---

## 11. Extensions du modèle de données (suite décisions)

### 11.1 Historique & état légal du véhicule

#### VehicleHistory

* id
* vehicle (FK)
* accident_history (TEXT)
* maintenance_history (TEXT)
* number_of_previous_owners
* last_inspection_date
* is_imported
* additional_notes

---

### 11.2 Soft Delete (global)

Tous les modèles métiers critiques implémentent :

* is_deleted (bool)
* deleted_at (datetime)

Exclusions par défaut via managers custom.

---

### 11.3 Logs & Audit

#### AuditLog

* id
* actor (FK user, nullable)
* action (CREATE | UPDATE | DELETE | LOGIN | PAYMENT)
* entity_type
* entity_id
* before_state (JSON)
* after_state (JSON)
* timestamp
* ip_address

Logs utilisés pour :

* audit légal
* debug
* traçabilité métier

---

## 12. Règles générales de conception

* Toute action métier significative génère un AuditLog
* Aucun delete physique sur les objets métier
* Accès API strictement contrôlé par rôle
* Admin Django = source de vérité manuelle

---

👉 **Le périmètre fonctionnel est maintenant verrouillé.**

Quand tu donneras le feu vert, le code minimal sera généré conformément à ces décisions.
