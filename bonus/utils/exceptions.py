from rest_framework.exceptions import APIException
from django.conf import settings


class EntityAlreadyExists(APIException):
    status_code = 409
    default_detail = 'Entity already exists.'


class AccountLimitExceeded(APIException):
    status_code = 403
    default_detail = 'Account limit exceeded.'


class MinBalanceLimit(APIException):
    status_code = 403
    default_detail = 'Minimum balance is ' + str(settings.MIN_ACCOUNT_BALANCE)


class BranchCloseMismatch(APIException):
    status_code = 400
    default_detail = 'User cannot close his account in this branch.'


class UnSettledLoan(APIException):
    status_code = 403
    default_detail = 'You have unsettled loans.'
