from django.urls import path, include, re_path
from .views import (
    LoginAPIView, RegistrationAPIView, UserRetrieveUpdateAPIView,
)
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('current', UserRetrieveUpdateAPIView.as_view()),
    path('register', RegistrationAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
    re_path('^', include(router.urls)),
]
