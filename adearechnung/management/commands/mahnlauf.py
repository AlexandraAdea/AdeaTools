from datetime import date

from django.core.management.base import BaseCommand, CommandError

from adearechnung import mahn_service
from adearechnung.mahnlogik import chf, d


class Command(BaseCommand):
    help = (
        "Prüft offene Rechnungen und erzeugt fällige Mahnungen. "
        "Ohne --ausfuehren wird nur angezeigt, was passieren würde (Trockenlauf)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--stichtag", help="YYYY-MM-DD, Standard: heute")
        parser.add_argument("--ausfuehren", action="store_true",
                            help="Mahnungen wirklich speichern (sonst Trockenlauf)")

    def handle(self, *args, **opts):
        try:
            stichtag = date.fromisoformat(opts["stichtag"]) if opts["stichtag"] else date.today()
        except ValueError as exc:
            raise CommandError("Stichtag muss im Format YYYY-MM-DD sein.") from exc

        ergebnisse = mahn_service.vorschau(stichtag)
        for e in ergebnisse:
            r = e.rechnung
            if e.aktion == "betreibung_pruefen":
                self.stdout.write(self.style.WARNING(
                    f"{r.nummer} {r.kunde}: alle Mahnstufen durchlaufen, Betreibung prüfen "
                    f"(offen {chf(e.offen)}, Total inkl. Zins/Gebühren {chf(e.total)})"))
            else:
                self.stdout.write(
                    f"{r.nummer} {r.kunde}: {e.stufe.name}, {e.tage_ueberfaellig} Tage überfällig, "
                    f"offen {chf(e.offen)} + Zins {chf(e.zins)} + Gebühren {chf(e.gebuehren)} "
                    f"= {chf(e.total)}, Frist {d(e.zahlungsfrist)}")

        if opts["ausfuehren"]:
            erzeugt, _ = mahn_service.mahnlauf_ausfuehren(stichtag)
            modus = f"{len(erzeugt)} Mahnung(en) gespeichert"
        else:
            modus = "Trockenlauf, nichts gespeichert"
        self.stdout.write(self.style.SUCCESS(f"{len(ergebnisse)} Vorgang/Vorgänge am {d(stichtag)} ({modus})."))
