from django.urls import path, include, re_path
from django.conf.urls import url
from .views import (
    LoginAPIView, RegistrationAPIView, UserRetrieveUpdateAPIView, StaffViewSet, BranchViewSet, AccountViewSet,
    TransactionViewSet, AccountCloseApiView, LoanViewSet
)
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'branch', BranchViewSet, basename='branch')
router.register(r'account', AccountViewSet, basename='account')
router.register(r'transaction', TransactionViewSet, basename='transaction')
router.register(r'loan', LoanViewSet, basename='loan')

urlpatterns = [
    url(r'^transaction/(?P<type>\w+)$', TransactionViewSet.as_view({'post': 'create'})),
    path('transaction', TransactionViewSet.as_view({'get': 'list'})),
    path('user', UserRetrieveUpdateAPIView.as_view()),
    path('register', RegistrationAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
    path('account/close', AccountCloseApiView.as_view()),
    re_path('^', include(router.urls)),
]
