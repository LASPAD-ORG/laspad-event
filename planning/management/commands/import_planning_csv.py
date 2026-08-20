"""Importe les événements du planning depuis un export CSV du Google Sheet du labo.

Usage :
    python manage.py import_planning_csv --url "https://docs.google.com/.../export?format=csv&gid=..."
    python manage.py import_planning_csv --file chemin/vers/planning.csv
    # option --replace : vide d'abord la table LabEvent avant d'importer.

Colonnes attendues (dans l'ordre du Sheet) :
    Projet, Type, Titre, Description, Date de début (JJ/MM/AAAA), Heure, Date de fin,
    Responsable, Invités, Besoins com, Besoin prod, Lieu, Status, (vide), Budget
"""
import csv
import datetime
import io
import urllib.request

from django.core.management.base import BaseCommand, CommandError

from planning.models import LabEvent


def _parse_date(s):
    s = (s or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _parse_time(s):
    s = (s or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.datetime.strptime(s, fmt).time()
        except ValueError:
            pass
    return None


def _map_status(raw):
    r = (raw or "").strip().lower()
    if not r:
        return "a_venir"
    if "annul" in r:
        return "annule"
    if "report" in r:
        return "reporte"
    if "fait" in r:
        return "fait"
    return "a_venir"


class Command(BaseCommand):
    help = "Importe les événements du planning depuis un CSV (URL Google Sheet ou fichier local)."

    def add_arguments(self, parser):
        parser.add_argument("--url", help="URL d'export CSV du Google Sheet.")
        parser.add_argument("--file", help="Chemin d'un fichier CSV local.")
        parser.add_argument("--replace", action="store_true",
                            help="Vide la table LabEvent avant d'importer.")

    def handle(self, *args, **opts):
        if not opts.get("url") and not opts.get("file"):
            raise CommandError("Fournissez --url ou --file.")

        if opts.get("file"):
            with open(opts["file"], encoding="utf-8") as fh:
                raw = fh.read()
        else:
            req = urllib.request.Request(opts["url"], headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

        rows = list(csv.reader(io.StringIO(raw)))
        if not rows:
            raise CommandError("CSV vide.")

        if opts.get("replace"):
            deleted, _ = LabEvent.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Table vidée ({deleted} lignes)."))

        created = skipped = 0
        for row in rows[1:]:  # saute l'en-tête
            if not any(c.strip() for c in row):
                continue
            row = row + [""] * (15 - len(row))
            (projet, type_e, titre, desc, d1, heure, d2, resp, invites,
             bcom, bprod, lieu, statut_raw, _x, budget) = row[:15]

            titre = titre.strip()
            date_debut = _parse_date(d1)
            if not titre or not date_debut:
                skipped += 1
                continue

            LabEvent.objects.create(
                projet=projet.strip(),
                type_event=(type_e.strip() or "Autre"),
                titre=titre,
                description=desc.strip(),
                date_debut=date_debut,
                heure=_parse_time(heure),
                date_fin=_parse_date(d2),
                responsable=resp.strip(),
                invites=invites.strip(),
                besoins_com=bcom.strip(),
                besoins_prod=bprod.strip(),
                lieu=lieu.strip(),
                statut=_map_status(statut_raw),
                budget=budget.strip(),
                created_by="import@laspad.org",
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import terminé : {created} événement(s) créé(s), {skipped} ignoré(s) (sans titre/date)."
        ))
