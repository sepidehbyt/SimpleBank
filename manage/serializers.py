from rest_framework import serializers
from .models import Branch, Bank
from identity.serializers import UserSerializer
from identity.models import User
from identity.enums import RoleType
from SimpleBank.utils import exceptions
from django.conf import settings
from rest_framework.serializers import PrimaryKeyRelatedField
import random
import string
from django.db.models import Q, Sum
import datetime
from dateutil.relativedelta import relativedelta


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
