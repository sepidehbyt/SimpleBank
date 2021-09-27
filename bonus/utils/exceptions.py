from rest_framework.exceptions import APIException


class EntityAlreadyExists(APIException):
    status_code = 409
    default_detail = 'Entity already exists.'
