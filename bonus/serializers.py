from abc import ABC

from rest_framework import serializers
from django.core.exceptions import PermissionDenied
from .models import User, Branch, Account, Bank, Transaction, Loan, Installment, UserStatistic
from django.contrib.auth import authenticate
from bonus.utils import exceptions
from django.conf import settings
from .enums import RoleType, TransactionType, RepaymentType
from rest_framework.serializers import PrimaryKeyRelatedField
import random
import string
from django.db.models import Q, Sum
import datetime
from dateutil.relativedelta import relativedelta


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=32, min_length=2)
    last_name = serializers.CharField(max_length=32, min_length=2)

    class Meta:
        model = User
        fields = ('id', 'mobile', 'first_name', 'last_name')
        read_only_fields = ('mobile', 'id')

    def update(self, instance, validated_data):
        for (key, value) in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        user_statistic = UserStatistic.objects.get(user=instance)
        user_statistic.name = instance.first_name + ' ' + instance.last_name
        user_statistic.save()
        return instance


class UserStatisticSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserStatistic
        fields = ['name', 'mobile', 'credit', 'debt', 'account_closed', 'loans_gotten', 'loans_unsettled']


class RegistrationSerializer(serializers.ModelSerializer):
    mobile = serializers.CharField(min_length=10, max_length=10)
    password = serializers.CharField(
        max_length=16,
        min_length=8,
        write_only=True,
        error_messages={'max_length': 'Password length must be lower that 16 characters.',
                        'min_length': 'Password length must be bigger that 8 characters.'})

    class Meta:
        model = User
        fields = ['id', 'mobile', 'password', 'first_name', 'last_name']

    def validate(self, data):
        mobile = data.get('mobile', None)
        password = data.get('password', None)

        if not User.objects.filter(mobile=User.objects.normalize_mobile(mobile)):
            return {'mobile': mobile, 'password': password}
        raise exceptions.EntityAlreadyExists()

    # an more complex validation on mobile
    def validate_mobile(self, value):
        if str(value[0]) != '9':
            raise serializers.ValidationError("Mobile field is not valid.")
        return value

    def create(self, validated_data):
        if validated_data.get('is_staff') is not None:
            return User.objects.create_superuser(**validated_data)
        return User.objects.create_user(**validated_data)


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['id', 'name']


class BranchSerializer(serializers.ModelSerializer):
    bank = BankSerializer()
    manager = UserSerializer()

    class Meta:
        model = Branch
        fields = ['id', 'name', 'bank', 'manager']


class BranchMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name']


class BranchCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=32, min_length=2)
    bank_id = PrimaryKeyRelatedField(queryset=Bank.objects.all(), required=True)
    manager_id = PrimaryKeyRelatedField(queryset=User.objects.filter(role=RoleType.BRANCH_MANAGER.value),
                                        required=True)

    class Meta:
        model = Branch
        fields = ['id', 'name', 'bank_id', 'manager_id']

    def validate(self, data):
        if not Branch.objects.filter(name=data.get('name')) and \
                not Branch.objects.filter(manager_id=data.get('manager_id')):
            return {'name': data.get('name'),
                    'bank': data.get('bank_id'),
                    'manager': data.get('manager_id')}
        raise exceptions.EntityAlreadyExists()

    def create(self, validated_data):
        return Branch.objects.create(**validated_data)


class LoginSerializer(serializers.Serializer):
    mobile = serializers.CharField(min_length=10, max_length=10)
    password = serializers.CharField(
        max_length=16,
        min_length=8,
        write_only=True,
        error_messages={'max_length': 'Password length must be lower that 16 characters.',
                        'min_length': 'Password length must be bigger that 8 characters.'})
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        mobile = data.get('mobile', None)
        password = data.get('password', None)

        user = authenticate(username=User.objects.normalize_mobile(mobile), password=password)

        if user is None:
            raise serializers.ValidationError("Mobile or Password is not correct.")

        return {
            'mobile': user.mobile,
            'token': user.token
        }


class AccountSerializer(serializers.ModelSerializer):
    src_branch = BranchMinimalSerializer()
    owner = UserSerializer()

    class Meta:
        model = Account
        fields = ['id', 'number', 'src_branch', 'owner', 'credit']


class AccountMinimalSerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = Account
        fields = ['number', 'owner']


class AccountCloseSerializer(serializers.ModelSerializer):
    src_branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=True)

    class Meta:
        model = Account
        fields = ['id', 'src_branch_id']

    def update_user_statistic(self, instance):
        user_statistic = UserStatistic.objects.get(user=instance.owner)
        user_statistic.account_closed = True
        user_statistic.save()

    def update(self, instance, validated_data):
        instance.is_active = False
        instance.save()
        self.update_user_statistic(instance)
        return instance


class AccountCreateSerializer(serializers.ModelSerializer):
    src_branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=True)

    class Meta:
        model = Account
        fields = ['id', 'number', 'src_branch_id', 'owner', 'credit']
        read_only_fields = ('number', 'owner')

    def validate(self, data):

        if not Account.objects.filter(owner=self.context.get('owner'), src_branch__bank=data.get('src_branch_id').bank):
            number = self.create_unique_id()
            unique = False
            while not unique:
                if not Account.objects.filter(number=number):
                    unique = True
                else:
                    number = create_unique_id()

            return {
                'number': number,
                'owner': self.context.get('owner'),
                'src_branch': data.get("src_branch_id"),
            }
        raise exceptions.EntityAlreadyExists()

    def create_unique_id(self):
        return ''.join(random.choices(string.digits, k=16))

    def create(self, validated_data):
        return Account.objects.create(**validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    src_account = AccountMinimalSerializer()
    dest_account = AccountMinimalSerializer()
    owner = UserSerializer()

    class Meta:
        model = Transaction
        fields = ['id', 'owner', 'src_account', 'dest_account', 'amount']


class TransactionCreateSerializer(serializers.ModelSerializer):
    src_account_id = PrimaryKeyRelatedField(queryset=Account.objects.filter(is_active=True), required=False)
    dest_account_id = PrimaryKeyRelatedField(queryset=Account.objects.filter(is_active=True), required=True)
    amount = serializers.IntegerField(min_value=int(settings.MIN_TRANSACTION_AMOUNT),
                                      max_value=int(settings.MAX_TRANSACTION_AMOUNT))

    class Meta:
        model = Transaction
        fields = ['id', 'src_account_id', 'dest_account_id', 'amount']

    def validate(self, data):
        # check total transaction amount
        owner = self.context.get('owner')
        amount = data.get('amount')
        dest_account = data.get('dest_account_id')
        src_account = data.get('src_account_id')
        if dest_account.owner != owner:
            raise serializers.ValidationError('This account does not belong to user.')
        total_transaction_amount = Transaction.objects.filter(created_at__gt=datetime.date.today(), owner=owner) \
            .aggregate(Sum('amount'))
        if total_transaction_amount['amount__sum'] is None:
            total_transaction_amount = 0
        else:
            total_transaction_amount = int(total_transaction_amount['amount__sum'])
        if total_transaction_amount + amount > int(settings.MAX_TRANSACTION_AMOUNT_DAILY):
            raise exceptions.AccountLimitExceeded
        if self.context.get('type') == TransactionType.DEPOSIT:
            # deposit cash to his own account
            if src_account is None:
                dest_account.credit = dest_account.credit + amount
                dest_account.save()
                transaction_type = TransactionType.DEPOSIT_CASH.value
                update_user_statistic(dest_account, +amount)
            # account to account deposit
            else:
                self.check_amount(src_account, amount)
                dest_account.credit = dest_account.credit + amount
                dest_account.save()
                src_account.credit = src_account.credit - amount
                src_account.save()
                transaction_type = TransactionType.DEPOSIT.value
                update_user_statistic(src_account, +amount)
                update_user_statistic(dest_account, -amount)
        else:
            # withdraw cash from his own account
            dest_account.credit = dest_account.credit + amount
            dest_account.save()
            transaction_type = TransactionType.WITHDRAW.value
            update_user_statistic(dest_account, -amount)

        return {'src_account': data.get('src_account_id'),
                'dest_account': data.get('dest_account_id'),
                'type': transaction_type,
                'owner': owner,
                'amount': amount,
                }

    def update_user_statistic(self, account, amount):
        user_statistic = UserStatistic.objects.get(user=account.owner)
        user_statistic.credit = user_statistic.credit + amount
        user_statistic.save()

    def check_amount(self, account, amount):
        if account.credit - amount < int(settings.MIN_ACCOUNT_BALANCE):
            raise exceptions.MinBalanceLimit

    def create(self, validated_data):
        return Transaction.objects.create(**validated_data)


class InstallmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Installment
        fields = ['id', 'amount', 'pay_date', 'is_settled']


class LoanSerializer(serializers.ModelSerializer):
    branch = BranchMinimalSerializer()
    installments = InstallmentSerializer(source='Installments_list', many=True)

    class Meta:
        model = Loan
        fields = ['id', 'branch', 'amount', 'type', 'is_settled', 'remainder_installment', 'installments']


class LoanCreateSerializer(serializers.ModelSerializer):
    branch_id = PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=True)
    amount = serializers.IntegerField(min_value=int(settings.MIN_LOAN_AMOUNT),
                                      max_value=int(settings.MAX_LOAN_AMOUNT))
    type = serializers.CharField(max_length=2)

    class Meta:
        model = Loan
        fields = ['id', 'branch_id', 'amount', 'type']

    def validate(self, data):
        return {'applicant': self.context.get('applicant'),
                'branch': data.get('branch_id'),
                'amount': data.get('amount'),
                'remainder_installment': data.get('amount'),
                'type': data.get('type')}

    def create_installments(self, loan):
        repayment_type = int(loan.type)
        amount = round(loan.amount / repayment_type)
        pay_date = datetime.date.today()
        one_month = relativedelta(months=1)
        for i in range(repayment_type):
            pay_date = pay_date + one_month
            installment = Installment(debtor=loan.applicant,
                                      loan=loan,
                                      amount=amount,
                                      pay_date=pay_date)
            installment.save()

    def update_user_statistics(self, loan):
        user_statistic = UserStatistic.objects.get(user=loan.applicant)
        user_statistic.loans_gotten = user_statistic.loans_gotten + 1
        user_statistic.loans_unsettled = user_statistic.loans_unsettled + 1
        user_statistic.debt = user_statistic.debt + loan.amount
        user_statistic.save()

    def create(self, validated_data):
        loan = Loan.objects.create(**validated_data)
        self.create_installments(loan)
        self.update_user_statistics(loan)
        return loan
