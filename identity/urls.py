from django.urls import path, include, re_path
from .views import (
    LoginAPIView, RegistrationAPIView, UserRetrieveUpdateAPIView, StaffViewSet, UserStatisticListView
)
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'staff', StaffViewSet, basename='staff')

urlpatterns = [
    path('', UserRetrieveUpdateAPIView.as_view()),
    path('statistic', UserStatisticListView.as_view()),
    path('register', RegistrationAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
    re_path('^', include(router.urls)),
]
