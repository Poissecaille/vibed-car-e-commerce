1. Client envoie POST /register {email, password}
       │
2. api.py reçoit → schemas.py valide les données
       │
3. api.py appelle → services.py (UserService.create_user)
       │
4. services.py appelle → User.objects.create_user() (Manager)
       │
5. Manager crée l'objet User et appelle → user.save()
       │
6. Django envoie signal post_save → signals.py crée le Profile
       │
7. Données persistées en base de données
