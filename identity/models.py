import jwt

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)

from django.db import models
from .enums import RoleType


class UserManager(BaseUserManager):

    def create_user(self, mobile, password):
        if mobile is None:
            raise TypeError('Users must enter mobile.')

        user = self.model(mobile=self.normalize_mobile(mobile))
        user.set_password(password)
        user.role = RoleType.USER.value
        user.save()

        return user

    def create_superuser(self, mobile, password, is_staff):
        if password is None:
            raise TypeError('Staff must have password.')

        user = self.create_user(mobile, password)
        user.is_staff = is_staff
        user.role = RoleType.BRANCH_MANAGER.value
        user.save()

        return user

    # assume we are all Iranian :D
    def normalize_mobile(self, mobile):
        return '+98' + (mobile.replace(" ", ""))[-10:]


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=32, unique=False, default='', blank=True)
    last_name = models.CharField(max_length=32, unique=False, default='', blank=True)
    mobile = models.CharField(max_length=13, unique=True, null=False)
    role = models.CharField(max_length=16, choices=[(r, r.value) for r in RoleType], default='USER')
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

        return jwt.encode({
            'mobile': self.mobile,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')


class UserStatistic(models.Model):
    name = models.CharField(max_length=64, default='Bonus Bank User', blank=False)
    mobile = models.CharField(max_length=13, unique=True, null=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credit = models.IntegerField(default=0)
    debt = models.IntegerField(default=0)
    account_closed = models.BooleanField(default=False)
    loans_gotten = models.IntegerField(default=0)
    loans_unsettled = models.IntegerField(default=0)
    # whatever more
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name
