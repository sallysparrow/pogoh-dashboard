from django.core.management.base import BaseCommand
from dashboard.views import set_station_status_log

class Command(BaseCommand):
    help = "Fetch current CityBikes data and store StationSnapshot rows."

    def handle(self, *args, **opts):
        set_station_status_log()
        self.stdout.write(self.style.SUCCESS("snapshots collected"))
