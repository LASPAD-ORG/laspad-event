import uuid
from django.db import models
from django.utils import timezone


class AuthorizedMember(models.Model):
    """Liste blanche : seuls ces e-mails peuvent se connecter au planning."""
    email      = models.EmailField(unique=True, verbose_name='E-mail')
    name       = models.CharField(max_length=150, blank=True, verbose_name='Nom')
    is_active  = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Membre autorisé'
        verbose_name_plural = 'Membres autorisés'
        ordering            = ['name', 'email']

    def __str__(self):
        return f"{self.name or self.email}"


class LoginToken(models.Model):
    """Jeton de connexion à usage unique (lien magique envoyé par e-mail)."""
    token      = models.CharField(max_length=64, unique=True, db_index=True)
    email      = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_at    = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        if self.used_at:
            return False
        # expire après 45 minutes
        return timezone.now() <= self.created_at + timezone.timedelta(minutes=45)

    def __str__(self):
        return f"{self.email} ({'utilisé' if self.used_at else 'actif'})"


class LabEvent(models.Model):
    """Un événement / activité du planning interne du labo."""

    STATUT_A_VENIR = 'a_venir'
    STATUT_FAIT    = 'fait'
    STATUT_REPORTE = 'reporte'
    STATUT_ANNULE  = 'annule'
    STATUT_CHOICES = [
        (STATUT_A_VENIR, 'À venir'),
        (STATUT_FAIT,    'Fait'),
        (STATUT_REPORTE, 'Reporté'),
        (STATUT_ANNULE,  'Annulé'),
    ]

    TYPE_CHOICES = [
        ('Formation',   'Formation'),
        ('Séminaire',   'Séminaire'),
        ('Réunion',     'Réunion'),
        ('Conférence',  'Conférence'),
        ('Atelier',     'Atelier'),
        ('Table ronde', 'Table ronde'),
        ('Tournage',    'Tournage'),
        ('Recrutement', 'Recrutement'),
        ('Autre',       'Autre'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projet       = models.CharField(max_length=150, blank=True, verbose_name='Projet')
    type_event   = models.CharField(max_length=40, choices=TYPE_CHOICES, default='Réunion', verbose_name='Type')
    titre        = models.CharField(max_length=300, verbose_name="Titre de l'événement")
    description  = models.TextField(blank=True, verbose_name='Description')
    date_debut   = models.DateField(verbose_name='Date de début')
    heure        = models.TimeField(null=True, blank=True, verbose_name='Heure')
    date_fin     = models.DateField(null=True, blank=True, verbose_name='Date de fin')
    responsable  = models.CharField(max_length=150, blank=True, verbose_name='Responsable')
    invites      = models.CharField(max_length=300, blank=True, verbose_name='Invités')
    besoins_com  = models.TextField(blank=True, verbose_name='Besoins de communication')
    besoins_prod = models.TextField(blank=True, verbose_name='Besoins de production')
    lieu         = models.CharField(max_length=200, blank=True, verbose_name='Lieu')
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_A_VENIR, verbose_name='Statut')
    budget       = models.CharField(max_length=100, blank=True, verbose_name='Budget validé')

    created_by   = models.EmailField(blank=True, verbose_name='Ajouté par')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Événement (planning)'
        verbose_name_plural = 'Événements (planning)'
        ordering            = ['date_debut', 'heure']

    def __str__(self):
        return f"{self.date_debut} — {self.titre}"
