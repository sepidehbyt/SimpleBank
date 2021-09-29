from django.conf import settings
from rest_framework.generics import RetrieveUpdateAPIView
from .models import User, UserStatistic
from django.shortcuts import get_object_or_404
from .serializers import LoginSerializer, RegistrationSerializer, UserSerializer, UserStatisticSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import viewsets
from SimpleBank.utils.bonusRenderer import BonusResponseRenderer
from .enums import RoleType
from SimpleBank.utils.smsService import manage_sms
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet


class UserStatisticListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = UserStatistic.objects.all()
    serializer_class = UserStatisticSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, )
    filterset_fields = ['name', 'mobile', 'credit', 'debt', 'account_closed', 'loans_gotten', 'loans_unsettled']
    ordering_fields = ['credit', 'debt', 'account_closed', 'loans_gotten', 'loans_unsettled']


class StaffViewSet(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = RegistrationSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def list(self, request):
        queryset = User.objects.filter(role='BRANCH_MANAGER')
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = User.objects.filter(role='BRANCH_MANAGER')
        user = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(is_staff=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            response = {'detail': serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        response = {}

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            response['detail'] = serializer.errors
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


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
            user = User.objects.get(pk=serializer.data['id'])
            user_statistic = UserStatistic(user=user, mobile=user.mobile, name=user.first_name+' '+user.last_name)
            user_statistic.save()
            manage_sms(user, None, 'welcome')
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
