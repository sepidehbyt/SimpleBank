from django.db import models
from identity.models import User


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
    manager = models.OneToOneField(User, on_delete=models.PROTECT, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name
