from django.urls import path
from .views import ChatAPIView, EmailAdvancedFilterAPIView

urlpatterns = [
    path('chat/', ChatAPIView.as_view(), name='chat-api'),
    path('emails/filter/', EmailAdvancedFilterAPIView.as_view(), name='emails-filter-api'),
]