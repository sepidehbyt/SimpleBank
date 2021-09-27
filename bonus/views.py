from django.shortcuts import render
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, CreateAPIView, UpdateAPIView
from .models import User
from .serializers import (
    LoginSerializer, RegistrationSerializer, UserSerializer,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from bonus.utils.bonusRenderer import BonusResponseRenderer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import math
import random
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import redirect
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
import datetime
import os


class BasicPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        data = serializer.data
        data.pop('id', None)
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer_data = request.data
        serializer = self.serializer_class(request.user, data=serializer_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        data.pop('id', None)

        return Response(data, status=status.HTTP_200_OK)


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        if type(user) is dict:
            return text_type(user['email']) + text_type(timestamp)
        return text_type(user.email) + text_type(timestamp)


class RegistrationAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegistrationSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def post(self, request):
        user = request.data
        response = {}

        serializer = self.serializer_class(data=user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            response['detail'] = serializer.errors
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def post(self, request):
        user = request.data
        response = {}

        serializer = self.serializer_class(data=user)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            response['detail'] = serializer.errors
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
