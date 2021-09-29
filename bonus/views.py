from django.shortcuts import render
from django.conf import settings
from bonus.utils import exceptions
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, CreateAPIView, UpdateAPIView
from .models import User, Branch, Bank, Account, Transaction, Loan, Installment
from .serializers import LoginSerializer, RegistrationSerializer, UserSerializer, BranchCreateSerializer,\
    BranchSerializer, AccountSerializer, AccountMinimalSerializer, AccountCreateSerializer, TransactionCreateSerializer,\
    TransactionSerializer, AccountCloseSerializer, LoanSerializer, LoanCreateSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import GenericViewSet
from bonus.utils.bonusRenderer import BonusResponseRenderer
from bonus.utils.customPermissions import IsRegularUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .enums import TransactionType
import math
import random
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import redirect
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
import datetime
import os
from bonus.utils.smsService import manage_sms


class BasicPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class StaffViewSet(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
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


class BranchViewSet(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = BranchCreateSerializer
    response_serializer_class = BranchSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def list(self, request):
        queryset = Branch.objects.filter(bank__id=request.user.bank.id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = Branch.objects.filter(bank__id=request.user.bank.id)
        branch = get_object_or_404(queryset, pk=pk)
        serializer = self.response_serializer_class(branch)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(self.response_serializer_class(Branch.objects.get(pk=serializer.data.get('id'))).data,
                            status=status.HTTP_201_CREATED)
        else:
            response = {'detail': serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class AccountViewSet(viewsets.ViewSet):
    permission_classes = (IsRegularUser,)
    serializer_class = AccountCreateSerializer
    response_serializer_class = AccountSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def list(self, request):
        if request.GET.get('number') is not None:
            queryset = Account.objects.filter(number=request.GET.get('number'), is_active=True)
            account = get_object_or_404(queryset)
            serializer = self.serializer_class(account)
        else:
            queryset = Account.objects.filter(owner=request.user, is_active=True)
            serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = Account.objects.filter(owner=request.user, is_active=True)
        branch = get_object_or_404(queryset, pk=pk)
        serializer = self.response_serializer_class(branch)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'owner': request.user})
        if serializer.is_valid():
            serializer.save()
            account = Account.objects.get(pk=serializer.data.get('id'))
            manage_sms(request.user, account, 'account')
            return Response(self.response_serializer_class(account).data,
                            status=status.HTTP_201_CREATED)
        else:
            response = {'detail': serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class AccountCloseApiView(APIView):
    permission_classes = (IsRegularUser,)
    serializer_class = AccountCloseSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def delete(self, request):
        queryset = Account.objects.filter(owner=request.user, is_active=True)
        account = get_object_or_404(queryset)
        loans = Loan.objects.filter(applicant=request.user, is_settled=False)
        if len(loans) > 0:
            raise exceptions.UnSettledLoan()
        serializer = self.serializer_class(account, data=request.data, partial=True)
        src_branch_id = request.data.get('src_branch_id')
        if src_branch_id == account.src_branch_id:
            raise exceptions.BranchCloseMismatch()
        if serializer.is_valid():
            serializer.save()
            return Response(None, status=status.HTTP_200_OK)
        else:
            esponse['detail'] = serializer.errors
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
            manage_sms(User.objects.get(pk=serializer.data['id']), None, 'welcome')
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


class TransactionViewSet(viewsets.ViewSet):
    permission_classes = (IsRegularUser,)
    serializer_class = TransactionCreateSerializer
    response_serializer_class = TransactionSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def list(self, request):
        c_get_tweets.delay()
        queryset = Transaction.objects.filter(Q(dest_account__owner=request.user)
                                              | Q(src_account__owner=request.user))
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, type):
        data = request.data
        response = {}

        if data.get('src_account_id') == data.get('dest_account_id'):
            response['detail'] = 'Source account and destination account are the same.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        if type == 'deposit':
            transaction_type = TransactionType.DEPOSIT
        elif type == 'withdraw':
            transaction_type = TransactionType.WITHDRAW
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(data=request.data, context={'type': transaction_type,
                                                                       'owner': request.user})
        if serializer.is_valid():
            serializer.save()
            transaction = Transaction.objects.get(pk=serializer.data.get('id'))
            manage_sms(request.user, transaction, 'transaction')
            return Response(self.response_serializer_class(transaction).data,
                            status=status.HTTP_201_CREATED)
        else:
            response = {'detail': serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class LoanViewSet(viewsets.ViewSet):
    permission_classes = (IsRegularUser,)
    serializer_class = LoanCreateSerializer
    response_serializer_class = LoanSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def list(self, request):
        queryset = Loan.objects.filter(applicant=request.user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = Loan.objects.filter(applicant=request.user)
        loan = get_object_or_404(queryset, pk=pk)
        serializer = self.response_serializer_class(loan)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'applicant': request.user})
        if serializer.is_valid():
            serializer.save()
            loan = Loan.objects.get(pk=serializer.data.get('id'))
            manage_sms(request.user, loan, 'loan')
            return Response(self.response_serializer_class(loan).data,
                            status=status.HTTP_201_CREATED)
        else:
            response = {'detail': serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
