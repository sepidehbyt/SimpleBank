from SimpleBank.utils import exceptions
from django.shortcuts import get_object_or_404
from identity.models import UserStatistic
from .models import Account, Transaction, Loan, Installment
from .serializers import AccountSerializer, AccountMinimalSerializer, AccountCreateSerializer,\
    TransactionCreateSerializer, TransactionSerializer, AccountCloseSerializer, LoanSerializer, LoanCreateSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import viewsets
from SimpleBank.utils.bonusRenderer import BonusResponseRenderer
from SimpleBank.utils.customPermissions import IsRegularUser, IsStaff
from .enums import TransactionType
from SimpleBank.utils.smsService import manage_sms
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet


class TransactionListView(generics.ListAPIView):
    permission_classes = [IsStaff]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, )
    filterset_fields = ['owner__mobile', 'src_account', 'src_account__owner', 'dest_account', 'dest_account__owner',
                        'amount', 'type']
    ordering_fields = ['amount', 'type']

    # in case to change
    def get_queryset(self):
        staff = self.request.user
        return Transaction.objects.all()


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
        queryset = Account.objects.filter(owner=request.user)
        account = get_object_or_404(queryset)
        serializer = self.serializer_class(data=request.data, context={'applicant': request.user})

        if serializer.is_valid():
            serializer.save()
            loan = Loan.objects.get(pk=serializer.data.get('id'))
            account.credit = account.credit + serializer.data.get('amount')
            account.save()
            manage_sms(request.user, loan, 'loan')
            return Response(self.response_serializer_class(loan).data,
                            status=status.HTTP_201_CREATED)
        else:
            response = {'detail': serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
