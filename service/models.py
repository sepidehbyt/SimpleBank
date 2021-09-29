from django.utils import timezone
from django.conf import settings
from django.db import models
from .enums import TransactionType, RepaymentType
from identity.models import User
from manage.models import Branch


class Account(models.Model):
    number = models.CharField(max_length=16, default='1111111111111111', unique=True, blank=False)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    src_branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    credit = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.owner


class Transaction(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT, default=1)
    src_account = models.ForeignKey(Account, related_name="src_accounts", on_delete=models.PROTECT, null=True)
    dest_account = models.ForeignKey(Account, related_name="dest_accounts", on_delete=models.PROTECT)
    amount = models.IntegerField(default=0)
    type = models.CharField(max_length=16, choices=[(t, t.value) for t in TransactionType])
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.owner


class Loan(models.Model):
    applicant = models.ForeignKey(User, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0, blank=False)
    is_settled = models.BooleanField(default=False)
    remainder_installment = models.IntegerField(default=0, blank=False)
    type = models.CharField(max_length=2, choices=[(r, r.value) for r in RepaymentType])
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.applicant


class Installment(models.Model):
    debtor = models.ForeignKey(User, on_delete=models.PROTECT)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="Installments_list")
    amount = models.IntegerField(default=0)
    is_settled = models.BooleanField(default=False)
    pay_date = models.DateTimeField(default=timezone.now, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.debtor
