from rest_framework import serializers
from .models import User, UserStatistic
from django.contrib.auth import authenticate
from SimpleBank.utils import exceptions
from django.conf import settings
from .enums import RoleType
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
