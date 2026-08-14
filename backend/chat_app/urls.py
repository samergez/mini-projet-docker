from django.urls import path
from .views import ChatAPIView, EmailAdvancedFilterAPIView, ExtractProjectsJSONAPIView, ExtractClientsJSONAPIView

urlpatterns = [
    path('chat/', ChatAPIView.as_view(), name='chat-api'),
    path('emails/filter/', EmailAdvancedFilterAPIView.as_view(), name='emails-filter-api'),
    path('extract-projects/', ExtractProjectsJSONAPIView.as_view(), name='extract-projects-api'),
    path('extract-clients/', ExtractClientsJSONAPIView.as_view(), name='extract-clients-api'),
]