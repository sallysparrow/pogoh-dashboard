from django.urls import path
from dashboard import consumers

websocket_urlpatterns = [
    path('dashboard/data', consumers.CommentConsumer.as_asgi()),
    path('dashboard/tour', consumers.TourConsumer.as_asgi()),
]