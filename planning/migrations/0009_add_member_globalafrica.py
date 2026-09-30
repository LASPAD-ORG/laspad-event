from django.db import migrations

# Ajout à la liste blanche (membres autorisés à se connecter au planning).
NEW_MEMBERS = [
    ("globalafrica@ugb.edu.sn", "Global Africa"),
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
        ("planning", "0008_add_member_koudous"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
