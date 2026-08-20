from django.db import migrations

# Corrige les noms affichés (e-mail de connexion « Bonjour … » + admin),
# d'après la liste officielle transmise par la communication du labo.
NAMES = {
    "diengmouhammad1607@gmail.com": "Mouhammad Dieng",
    "administration@laspad.org":    "Ndeye Madjiguène Diouf",
    "dykhadiop5@gmail.com":         "Ndèye Khady Diop",
    "papa-fara.diallo@ugb.edu.sn":  "Papa Fara Diallo",
    "papaseydou.wane@unchk.edu.sn": "Papa Seydou Wane",
    "rakygueye@esp.sn":             "Raky Gueye",
    "diopramasao@gmail.com":        "Rama Diop",
    "sokhna.ndiaye@urdfs.edu.sn":   "Sokhna Rosalie Ndiaye",
    "stwashjc@gmail.com":           "Stanislas Gomes",
    "amoussatekiyath2@gmail.com":   "Tèkiyath Amoussa",
    "zeynab.lasp@gmail.com":        "Zeynab",
    "dieynaba1411@gmail.com":       "Dieynaba Ba",
    "niangfatoubinetou@gmail.com":  "Fatou Binetou Niang",
    "mame-penda.ba@ugb.edu.sn":     "Mame-Penda Ba",
    "mldc1618@gmail.com":           "Mamadou Lamine Diandy",
}


def fix_names(apps, schema_editor):
    AuthorizedMember = apps.get_model("planning", "AuthorizedMember")
    for email, name in NAMES.items():
        AuthorizedMember.objects.filter(email__iexact=email).update(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("planning", "0003_add_communication"),
    ]

    operations = [
        migrations.RunPython(fix_names, migrations.RunPython.noop),
    ]
