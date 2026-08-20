from django.db import migrations

# Liste blanche initiale des membres du labo autorisés à se connecter au planning.
# Idempotent : on ne crée que ceux qui manquent, on ne touche pas aux existants.
MEMBERS = [
    ("adjadiop787@gmail.com", "Adja Diop"),
    ("administration@laspad.org", "Administration LASPAD"),
    ("amadoucire.sall@gmail.com", "Amadou Cire Sall"),
    ("amoussatekiyath2@gmail.com", "Amoussa Tekiyath"),
    ("ayrton.aubry@sciencespo.fr", "Ayrton Aubry"),
    ("bintoufrankaly@gmail.com", "Bintou Frankaly"),
    ("ciss9619@gmail.com", "Ciss"),
    ("cissebabacar717@gmail.com", "Babacar Cissé"),
    ("diengmouhammad1607@gmail.com", "Mouhammad Dieng"),
    ("dieynaba1411@gmail.com", "Dieynaba"),
    ("diopramasao@gmail.com", "Rama Sao Diop"),
    ("dykhadiop5@gmail.com", "Dykha Diop"),
    ("fatimatoudia@gmail.com", "Fatimatou Dia"),
    ("mame-penda.ba@ugb.edu.sn", "Mame-Penda Ba"),
    ("mldc1618@gmail.com", "Mamadou Lamine Diandy"),
    ("modedieng@gmail.com", "Mode Dieng"),
    ("niangfatoubinetou@gmail.com", "Fatou Binetou Niang"),
    ("papa-fara.diallo@ugb.edu.sn", "Papa Fara Diallo"),
    ("papaseydou.wane@unchk.edu.sn", "Papa Seydou Wane"),
    ("rakygueye@esp.sn", "Raky Guèye"),
    ("sokhna.ndiaye@urdfs.edu.sn", "Sokhna Ndiaye"),
    ("stwashjc@gmail.com", "Stanislas Gomes"),
    ("zeynab.lasp@gmail.com", "Zeynab"),
]


def seed(apps, schema_editor):
    AuthorizedMember = apps.get_model("planning", "AuthorizedMember")
    for email, name in MEMBERS:
        AuthorizedMember.objects.get_or_create(
            email=email.lower(),
            defaults={"name": name, "is_active": True},
        )


def unseed(apps, schema_editor):
    # Réversible : on retire uniquement les e-mails de cette liste.
    AuthorizedMember = apps.get_model("planning", "AuthorizedMember")
    emails = [e.lower() for e, _ in MEMBERS]
    AuthorizedMember.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("planning", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
