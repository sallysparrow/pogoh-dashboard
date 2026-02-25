from datetime import datetime, timedelta, timezone as dt_timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg
from django.db.models.functions import TruncHour
from django.views.decorators.http import require_GET
from django.db.models.functions import TruncHour, TruncDate

from dashboard.forms import LoginForm, RegisterForm
from dashboard.models import Station, StationStatusLog, Comment

from .models import StationSnapshot  
from datetime import timedelta

# Make requests optional so Django checks/migrations don't fail
try:
    import requests
except ImportError:
    requests = None


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard_overview')
    return redirect('login')


# --------- bootstrap helpers (optional) ----------

def fetch_data():
    if requests is None:
        raise RuntimeError("requests is not installed.")
    response = requests.get("https://api.citybik.es/v2/networks/pittsburgh", timeout=10)
    response.raise_for_status()
    return response.json()


def set_stations():
    if requests is None:
        return
    data = fetch_data()
    stations = data["network"]["stations"]
    for s in stations:
        Station.objects.update_or_create(
            name=s["name"],
            defaults={
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "slots": s["extra"].get("slots", 0),
            },
        )


def is_empty(free_bikes):
    return free_bikes == 0


def is_full(empty_slots):
    return empty_slots == 0


def set_station_status_log():
    if requests is None:
        return
    data = fetch_data()
    stations = data["network"]["stations"]

    for s in stations:
        station = Station.objects.filter(name=s["name"]).first()
        if not station:
            continue
        StationStatusLog.objects.create(
            date=timezone.now().date(),
            time=timezone.now().time(),
            empty_slots=s["empty_slots"],
            free_bikes=s["free_bikes"],
            empty=is_empty(s["free_bikes"]),
            full=is_full(s["empty_slots"]),
            station=station,
        )
    
        # write the snapshot row used by the trend chart
        StationSnapshot.objects.create(
            station=station,
            timestamp=timezone.now(),  
            free_bikes=s["free_bikes"],
            empty_slots=s["empty_slots"],
        )



# -------------------- Authentication --------------------

def login_view(request):
    if request.method == 'GET':
        return render(request, 'dashboard/login.html', {'form': LoginForm()})

    form = LoginForm(request.POST)
    if not form.is_valid():
        return render(request, 'dashboard/login.html', {'form': form})

    user = authenticate(
        username=form.cleaned_data['username'],
        password=form.cleaned_data['password']
    )
    login(request, user)
    return redirect('dashboard_overview')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'GET':
        return render(request, 'dashboard/register.html', {'form': RegisterForm()})

    form = RegisterForm(request.POST)
    if not form.is_valid():
        return render(request, 'dashboard/register.html', {'form': form})

    user = User.objects.create_user(
        username=form.cleaned_data['username'],
        password=form.cleaned_data['password'],
        email=form.cleaned_data['email'],
        first_name=form.cleaned_data['first_name'],
        last_name=form.cleaned_data['last_name'],
    )
    login(request, user)
    return redirect('dashboard_overview')


# -------------------- Pages --------------------

@login_required
def overview_view(request):
    return render(request, 'dashboard/overview.html')


@login_required
def station_detail_page(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    return render(request, 'dashboard/station_detail.html', {"station": station})

@login_required
def tour_view(request):
    return render(request, 'dashboard/tour.html')



# -------------------- APIs --------------------

@login_required
def stations_api(request):
    stations = Station.objects.all().order_by('name')
    payload = []

    for s in stations:
        log = (
            StationStatusLog.objects.filter(station=s)
            .order_by('-date', '-time')
            .first()
        )
        if log:
            free_bikes = log.free_bikes
            empty_slots = log.empty_slots
        else:
            free_bikes = 0
            # assume unknown empties => capacity = slots
            empty_slots = max(s.slots - free_bikes, 0)

        capacity = free_bikes + empty_slots or s.slots or 1
        pct_full = round(100 * free_bikes / capacity)

        if free_bikes == 0:
            status = "empty"
        elif empty_slots == 0:
            status = "full"
        else:
            status = "between"

        payload.append(
            {
                "id": s.id,
                "name": s.name,
                "latitude": float(s.latitude),
                "longitude": float(s.longitude),
                "slots": s.slots,
                "free_bikes": free_bikes,
                "empty_slots": empty_slots,
                "pct_full": pct_full,
                "status": status,
            }
        )

    return JsonResponse({"stations": payload})


@login_required
def station_detail_api(request, station_id):
    s = get_object_or_404(Station, pk=station_id)
    log = (
        StationStatusLog.objects.filter(station=s)
        .order_by('-date', '-time')
        .first()
    )
    if log:
        free_bikes = log.free_bikes
        empty_slots = log.empty_slots
    else:
        free_bikes = 0
        empty_slots = max(s.slots - free_bikes, 0)

    capacity = free_bikes + empty_slots or s.slots or 1
    pct_full = round(100 * free_bikes / capacity)

    return JsonResponse(
        {
            "id": s.id,
            "name": s.name,
            "slots": s.slots,
            "free_bikes": free_bikes,
            "empty_slots": empty_slots,
            "pct_full": pct_full,
        }
    )


@login_required
def station_trend_api(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    logs = (
        StationStatusLog.objects.filter(station=station)
        .order_by('-date', '-time')[:24]
    )
    logs = list(reversed(logs))
    labels = [l.time.strftime('%H:%M') for l in logs]
    values = [l.free_bikes for l in logs]
    return JsonResponse({"labels": labels, "values": values})


@login_required
def station_comments_api(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    comments = (
        Comment.objects.filter(commented_to=station)
        .order_by('-creation_time')[:20]
    )
    data = [
        {
            "id": c.id,
            "author": c.name,
            "content": c.content,
            "time": timezone.localtime(c.creation_time).strftime("%H:%M"),
        }
        for c in comments
    ]
    return JsonResponse({"comments": data})


@login_required
@require_POST
def add_comment_api(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse({"error": "Empty comment."}, status=400)

    c = Comment.objects.create(
        commented_to=station,
        commentor=request.user,
        content=content,
        name=request.user.username,
        creation_time=timezone.now(),
    )
    return JsonResponse(
        {
            "id": c.id,
            "author": c.name,
            "content": c.content,
            "time": timezone.localtime(c.creation_time).strftime("%H:%M"),
        }
    )

@login_required
def stations_api(request):
    # If no stations yet, try to seed once from CityBikes (if 'requests' is available)
    if not Station.objects.exists() and requests is not None:
        try:
            set_stations()
            set_station_status_log()
        except Exception:
            # On failure, continue with whatever data exists (likely none)
            pass

    stations = Station.objects.all().order_by('name')
    payload = []

    for s in stations:
        # Latest status log for this station
        log = (
            StationStatusLog.objects.filter(station=s)
            .order_by('-date', '-time')
            .first()
        )

        if log:
            free_bikes = log.free_bikes
            empty_slots = log.empty_slots
        else:
            # Fallback if no logs: assume zero bikes (still renders markers)
            free_bikes = 0
            empty_slots = max(s.slots - free_bikes, 0)

        capacity = free_bikes + empty_slots or s.slots or 1
        pct_full = round(100 * free_bikes / capacity)

        if pct_full == 0:
            status = "bad_empty"
        elif pct_full <= 15:
            status = "low"
        elif pct_full <= 75:
            status = "ok"
        elif pct_full <= 90:
            status = "high"
        elif pct_full >= 100:
            status = "bad_full"
        else:
            status = "ok"

        payload.append({
            "id": s.id,
            "name": s.name,
            "latitude": float(s.latitude),
            "longitude": float(s.longitude),
            "slots": s.slots,
            "free_bikes": free_bikes,
            "empty_slots": empty_slots,
            "pct_full": pct_full,
            "status": status,
        })

    return JsonResponse({"stations": payload})


@require_GET
def station_trend(request, station_id: int):

    # ---- fixed 24-hour window ---------------------------------------------
    FIXED_DAY = datetime(2025, 11, 18, tzinfo=dt_timezone.utc)
    start     = FIXED_DAY
    end       = FIXED_DAY + timedelta(hours=24)

    hourly_qs = (
        StationSnapshot.objects
        .filter(station_id=station_id,
                timestamp__gte=start,
                timestamp__lt=end)
        .annotate(bucket=TruncHour("timestamp"))
        .values("bucket")
        .annotate(free=Avg("free_bikes"))
        .order_by("bucket")
    )

    if hourly_qs.exists():
        series = [{"ts": r["bucket"].isoformat(), "free": r["free"]} for r in hourly_qs]
        return JsonResponse({"granularity": "hour", "series": series})

    # ---- fallback: one daily point for the same date -----------------------
    daily_qs = (
        StationSnapshot.objects
        .filter(station_id=station_id,
                timestamp__date=FIXED_DAY.date())
        .annotate(bucket=TruncDate("timestamp"))
        .values("bucket")
        .annotate(free=Avg("free_bikes"))
    )

    series = [{"ts": r["bucket"].isoformat(), "free": r["free"]} for r in daily_qs]
    return JsonResponse({"granularity": "day", "series": series})