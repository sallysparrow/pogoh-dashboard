from datetime import datetime, timedelta
from random import randint

from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.models import Station, StationSnapshot


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            help="YYYY-MM-DD (UTC). Defaults to yesterday.",
        )

    @staticmethod
    def _day_start(day_str: str | None) -> datetime:
        if day_str:
            # interpret in UTC
            return datetime.fromisoformat(day_str).replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
        # yesterday, UTC
        return (timezone.now() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def handle(self, *args, date=None, **opts):
        day_start = self._day_start(date)
        stations = Station.objects.all()

        total_inserted = 0
        for st in stations:
            # clear any existing snapshots for that day
            StationSnapshot.objects.filter(
                station=st, timestamp__date=day_start.date()
            ).delete()

            slots = st.slots or 20  # fallback if slots is null/zero
            snapshots = []
            for h in range(24):
                ts = day_start + timedelta(hours=h)
                free = randint(0, slots)
                snapshots.append(
                    StationSnapshot(
                        station=st,
                        timestamp=ts,
                        free_bikes=free,
                        empty_slots=max(slots - free, 0),
                    )
                )
            StationSnapshot.objects.bulk_create(snapshots)
            total_inserted += len(snapshots)

        self.stdout.write(
            self.style.SUCCESS(
                f"{total_inserted} snapshots inserted "
                f"for {stations.count()} stations on {day_start.date()}."
            )
        )
