from django.urls import re_path, include
from .views import BranchViewSet
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'branch', BranchViewSet, basename='branch')

urlpatterns = [
    re_path('^', include(router.urls)),
]
