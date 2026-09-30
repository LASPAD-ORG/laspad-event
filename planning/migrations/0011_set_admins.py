from django.db import migrations

# Membres administrateurs : peuvent générer un lien de connexion pour un autre
# membre (à envoyer par WhatsApp), en plus de l'usage normal.
ADMINS = [
    "communication@laspad.org",
    "administration@laspad.org",
]


def set_admins(apps, schema_editor):
    AuthorizedMember = apps.get_model("planning", "AuthorizedMember")
    AuthorizedMember.objects.filter(email__in=[e.lower() for e in ADMINS]).update(is_admin=True)


def unset_admins(apps, schema_editor):
    AuthorizedMember = apps.get_model("planning", "AuthorizedMember")
    AuthorizedMember.objects.filter(email__in=[e.lower() for e in ADMINS]).update(is_admin=False)


class Migration(migrations.Migration):

    dependencies = [
        ("planning", "0010_authorizedmember_is_admin_logintoken_ttl_minutes"),
    ]

    operations = [
        migrations.RunPython(set_admins, unset_admins),
    ]
