from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Pages
    path('dashboard/', views.overview_view, name='dashboard_overview'),
    path('dashboard/station/<int:station_id>/', views.station_detail_page, name='dashboard_station_detail'),
    path('tour/', views.tour_view, name='tour'),

    # APIs
    path('api/stations/', views.stations_api, name='stations_api'),
    path('api/stations/<int:station_id>/', views.station_detail_api, name='station_detail_api'),
    path('api/stations/<int:station_id>/comments/', views.station_comments_api, name='station_comments_api'),
    path('api/stations/<int:station_id>/comments/add/', views.add_comment_api, name='add_comment_api'),
    path("api/stations/<int:station_id>/trend/", views.station_trend, name="station_trend"),
    ]
