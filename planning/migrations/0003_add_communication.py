from django.db import migrations

# Ajouts à la liste blanche (membres autorisés à se connecter au planning).
# Idempotent : on ne crée que ceux qui manquent.
NEW_MEMBERS = [
    ("communication@laspad.org", "Communication LASPAD"),
]


def seed(apps, schema_editor):
    AuthorizedMember = apps.get_model("planning", "AuthorizedMember")
    for email, name in NEW_MEMBERS:
        AuthorizedMember.objects.get_or_create(
            email=email.lower(),
            defaults={"name": name, "is_active": True},
        )


def unseed(apps, schema_editor):
    AuthorizedMember = apps.get_model("planning", "AuthorizedMember")
    emails = [e.lower() for e, _ in NEW_MEMBERS]
    AuthorizedMember.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("planning", "0002_seed_members"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
