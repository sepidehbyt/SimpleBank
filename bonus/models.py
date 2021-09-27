import jwt

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)

from django.db import models
from .enums import TransactionType, RepaymentType


class UserManager(BaseUserManager):

    def create_user(self, mobile, password=None):
        if mobile is None:
            raise TypeError('Users must enter mobile.')

        user = self.model(mobile=self.normalize_mobile(mobile))
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password):
        if password is None:
            raise TypeError('Staff must have password.')

        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user

    # assume we are all Iranian :D
    def normalize_mobile(self, mobile):
        return '+98' + (mobile.replace(" ", ""))[-10:]


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=32, unique=False, default='', blank=True)
    last_name = models.CharField(max_length=32, unique=False, default='', blank=True)
    mobile = models.CharField(max_length=13, unique=True, null=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    USERNAME_FIELD = 'mobile'

    objects = UserManager()

    def __str__(self):
        return self.mobile

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        dt = datetime.now() + timedelta(days=60)

        token = jwt.encode({
            'mobile': self.mobile,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')


class Bank(models.Model):
    name = models.CharField(max_length=32, unique=True, default='Bonus', blank=False)
    owner = models.OneToOneField(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=32, unique=True, default='Bonus Branch #1', blank=False)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, blank=False)
    manager = models.ForeignKey(User, on_delete=models.PROTECT, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name


class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    src_branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    credit = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.owner


class Transaction(models.Model):
    src_account = models.ForeignKey(Account, related_name="src_accounts", on_delete=models.PROTECT)
    dest_account = models.ForeignKey(Account, related_name="dest_accounts", on_delete=models.PROTECT)
    amount = models.IntegerField(default=0)
    type = models.CharField(max_length=8, choices=[(t, t.value) for t in TransactionType])
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.owner


class Loan(models.Model):
    applicant = models.ForeignKey(User, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0, blank=False)
    is_settled = models.BooleanField(default=False)
    remainder_installment = models.IntegerField(default=12, blank=False)
    type = models.CharField(max_length=12, choices=[(r, r.value) for r in RepaymentType])
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.applicant


class Installment(models.Model):
    debtor = models.ForeignKey(User, on_delete=models.PROTECT)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    is_settled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.debtor
